import json
import re
import requests

from galaxy_classification.database import GalaxyDatabase


class ChatService:
    def __init__(self):
        self.OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

        self.SQL_MODEL = "sqlcoder:7b"
        self.CHAT_MODEL = "qwen3:8b"

        self.db = GalaxyDatabase()

    def _call_ollama(
        self,
        model,
        prompt,
        stream=False,
        temperature=0.2
    ):
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature
            }
        }

        return requests.post(
            self.OLLAMA_URL,
            json=payload,
            stream=stream,
            timeout=60
        )

    def generate_sql_query(self, user_message: str):
        """
        Generate SQL query from natural language.
        """

        schema_info = self.db.get_schema_info()

        system_prompt = f"""
Generate ONE valid SQLite SELECT query.

Schema:
{schema_info}

Rules:
- Only SELECT queries
- SQLite syntax only
- No markdown
- No explanations
- Use JOIN when needed
- Return ONLY SQL

Question:
{user_message}

SQL:
"""

        try:
            response = self._call_ollama(
                model=self.SQL_MODEL,
                prompt=system_prompt,
                stream=False,
                temperature=0
            )

            response.raise_for_status()

            result = response.json()

            full_response = (
                result.get("response")
                or result.get("results")
                or result.get("text")
                or ""
            )

            sql = full_response.strip()

            sql = sql.replace("```sql", "")
            sql = sql.replace("```", "")
            sql = sql.strip()

            sql = re.sub(r"^SQL:\s*", "", sql, flags=re.IGNORECASE)

            if not sql.lower().startswith("select"):
                return {
                    "success": False,
                    "sql": None,
                    "explanation": full_response,
                    "error": "Model did not return valid SELECT query"
                }

            return {
                "success": True,
                "sql": sql,
                "explanation": "SQL query generated successfully",
                "error": None
            }

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "sql": None,
                "explanation": None,
                "error": "Ollama server not detected. Ensure 'ollama serve' is running."
            }

        except Exception as e:
            return {
                "success": False,
                "sql": None,
                "explanation": None,
                "error": f"Error generating SQL: {str(e)}"
            }

    def get_dynamic_database_response(self, user_message):
        """
        Generate SQL from user message and execute it.
        """

        sql_result = self.generate_sql_query(user_message)

        if not sql_result["success"]:

            response = self.get_database_response(user_message)

            if response is not None:
                return response

            return (
                f"Failed to generate SQL query.\n"
                f"Reason: {sql_result['error']}\n\n"
                f"Model response:\n{sql_result['explanation']}"
            )

        execution = self.db.execute_query(sql_result["sql"])

        if not execution["success"]:
            return (
                f"SQL execution failed:\n"
                f"{execution['error']}\n\n"
                f"SQL:\n{sql_result['sql']}"
            )

        return self._format_query_results(
            sql_result["sql"],
            execution
        )

    def _format_query_results(self, sql, execution):

        if execution["count"] == 0:
            return (
                f"Executed SQL:\n{sql}\n\n"
                f"No rows returned."
            )

        lines = [
            f"Executed SQL:\n{sql}",
            f"",
            f"Returned {execution['count']} row(s):"
        ]

        if execution["columns"]:
            header = " | ".join(execution["columns"])
            lines.append(header)
            lines.append("-" * len(header))

        for row in execution["rows"]:
            row_text = " | ".join(
                str(row.get(col, ""))
                for col in execution["columns"]
            )
            lines.append(row_text)

        return "\n".join(lines)

    def get_database_response(self, user_message):

        message = (user_message or "").strip()
        lower = message.lower()

        observation_id = self._extract_observation_id(message)

        if observation_id:

            observation = self.db.get_observation_by_id(
                observation_id
            )

            if observation:
                return self._format_observation_detail(
                    observation
                )

            return (
                f"No local observation found "
                f"with id `{observation_id}`."
            )

        wants_database = any(
            term in lower for term in (
                "database",
                "db",
                "observation",
                "observations",
                "dossier",
                "dossiers",
                "record",
                "records",
                "captured",
                "classification",
                "classifications",
                "confidence",
                "redshift",
                "metadata",
                "model"
            )
        )

        if not wants_database:
            return None

        if any(
            term in lower for term in (
                "how many",
                "count",
                "total",
                "stats",
                "statistics",
                "distribution"
            )
        ):
            return self._format_database_stats()

        if any(
            term in lower for term in (
                "latest",
                "last",
                "newest",
                "most recent"
            )
        ):
            latest_id = self.db.get_latest_observation_id()

            if not latest_id:
                return (
                    "No local observations "
                    "are currently stored."
                )

            observation = self.db.get_observation_by_id(
                latest_id
            )

            return self._format_observation_detail(
                observation
            )

        if any(
            term in lower for term in (
                "list",
                "show",
                "recent",
                "records",
                "dossiers",
                "observations"
            )
        ):
            limit = self._extract_limit(
                lower,
                default=10
            )

            return self._format_recent_observations(
                limit
            )

        return self._format_database_overview()

    def generate_response(
        self,
        user_message,
        session_id="default",
        mode="expert"
    ):

        if mode == "database":

            database_context = self._format_database_overview()

            system_persona = (
                "You are the GCS database assistant "
                "for a galaxy classification app. "
                "Be concise and technical. "
                "Do not invent local observations, "
                "metadata, coordinates, redshifts, "
                "confidence values, or model versions.\n\n"
                "Current database context:\n"
                f"{database_context}"
            )

        else:
            system_persona = (
                "You are an expert astrophysicist "
                "specialized in galaxy classification, "
                "deep learning, and astronomy.\n"
                "Provide scientifically accurate answers.\n"
                "Do not invent database records.\n"
            )

        prompt = (
            f"<|begin_of_text|>"
            f"<|start_header_id|>system<|end_header_id|>\n\n"
            f"{system_persona}"
            f"<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|>\n\n"
            f"{user_message}"
            f"<|eot_id|>"
            f"<|start_header_id|>assistant<|end_header_id|>\n\n"
        )

        def generate():
            try:
                with self._call_ollama(
                    model=self.CHAT_MODEL,
                    prompt=prompt,
                    stream=True,
                    temperature=0.4
                ) as r:
                    r.raise_for_status()

                    for line in r.iter_lines():

                        if line:
                            chunk = json.loads(
                                line.decode("utf-8")
                            )
                            token = chunk.get(
                                "response",
                                ""
                            )
                            yield token
                            if chunk.get("done"):
                                break
            except requests.exceptions.ConnectionError:
                yield (
                    "[Error: Ollama server not detected. "
                    "Ensure 'ollama serve' is running.]"
                )
            except Exception as e:

                yield f"[System Error: {str(e)}]"

        return generate()

    def _extract_observation_id(self, message):

        match = re.search(
            r"\bGCSO-[A-Z0-9]+\b",
            message,
            re.IGNORECASE
        )

        return match.group(0).upper() if match else None

    def _extract_limit(self, message, default=10):

        match = re.search(r"\b(\d{1,2})\b", message)

        if not match:
            return default

        return max(
            1,
            min(int(match.group(1)), 25)
        )

    def _format_database_stats(self):

        total = self.db.get_observation_count()

        classified = (
            self.db.get_classified_observation_count()
        )

        stats = self.db.get_classification_stats()

        lines = [
            "LOCAL_DATABASE_STATS",
            f"- Total observations: {total}",
            f"- Classified observations: {classified}",
        ]

        if stats:

            lines.append(
                "- Classification distribution:"
            )

            for row in stats:

                avg = row["avg_confidence"]

                avg_text = (
                    f"{avg * 100:.1f}%"
                    if avg is not None
                    else "N/A"
                )

                lines.append(
                    f"  - {row['class']}: "
                    f"{row['count']} records, "
                    f"avg confidence {avg_text}"
                )

        else:

            lines.append(
                "- Classification distribution: "
                "no classified records"
            )

        return "\n".join(lines)

    def _format_recent_observations(self, limit):

        observations = self.db.get_recent_observations(
            limit
        )

        if not observations:

            return (
                "No classified observations are "
                "currently stored in the local database."
            )

        lines = [
            f"RECENT_OBSERVATIONS_LIMIT_{limit}"
        ]

        for obs in observations:

            confidence = obs["confidence"]

            confidence_text = (
                f"{confidence * 100:.1f}%"
                if confidence is not None
                else "N/A"
            )

            lines.append(
                f"- {obs['observation_id']} | "
                f"class={obs['predicted_class'] or 'N/A'} | "
                f"confidence={confidence_text} | "
                f"RA={obs['ra']:.5f} "
                f"DEC={obs['dec']:.5f} | "
                f"survey={obs['survey_source']}"
            )

        return "\n".join(lines)

    def _format_database_overview(self):

        total = self.db.get_observation_count()

        classified = (
            self.db.get_classified_observation_count()
        )

        recent = (
            self.db.get_recent_observations_summary(5)
        )

        return (
            f"Total observations: {total}\n"
            f"Classified observations: {classified}\n"
            f"Recent records:\n{recent}"
        )

    def _format_observation_detail(self, obs):

        if not obs:
            return "No local observation found."

        confidence = obs.get("confidence")

        confidence_text = (
            f"{confidence * 100:.1f}%"
            if confidence is not None
            else "N/A"
        )

        metadata = obs.get("metadata_json") or {}

        lines = [
            f"OBSERVATION_DETAIL {obs.get('observation_id')}",
            f"- Internal id: {obs.get('id')}",
            f"- Coordinates: "
            f"RA={obs.get('ra'):.5f}, "
            f"DEC={obs.get('dec'):.5f}",
            f"- Survey source: "
            f"{obs.get('survey_source') or 'N/A'}",
            f"- Captured at: "
            f"{obs.get('captured_at') or 'N/A'}",
            f"- Classification: "
            f"{obs.get('predicted_class') or 'N/A'}",
            f"- Confidence: {confidence_text}",
            f"- Model version: "
            f"{obs.get('model_version') or 'N/A'}",
            f"- Manual override: "
            f"{'yes' if obs.get('is_manual_override') else 'no'}",
            f"- Object type: "
            f"{obs.get('object_type') or 'N/A'}",
            f"- Redshift: "
            f"{self._format_value(obs.get('redshift'))}",
        ]

        if metadata:

            lines.extend([
                f"- SDSS phot_objid: "
                f"{self._format_value(metadata.get('phot_objid'))}",

                f"- SDSS specobjid: "
                f"{self._format_value(metadata.get('specobjid'))}",

                f"- SDSS subclass: "
                f"{self._format_value(metadata.get('subClass'))}",
            ])

        return "\n".join(lines)

    def _format_value(self, value):

        if value is None or value == "":
            return "N/A"

        if isinstance(value, float):
            return f"{value:.5f}"

        return str(value)