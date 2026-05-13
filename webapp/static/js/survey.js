const INITIAL_FOV = 0.12;
const TILE_SETTLE_MS = 1200;

let aladin;
let captureReadyAt = 0;
let captureReadyTimer = null;

document.addEventListener('DOMContentLoaded', () => {
    const progressBar = document.getElementById('progress-bar');
    const loaderStatus = document.getElementById('loader-status');
    const loaderLogs = document.getElementById('loader-logs');

    if (progressBar) progressBar.style.width = '35%';
    if (loaderStatus) loaderStatus.innerText = 'WAITING_FOR_ALADIN_CORE...';
    if (loaderLogs) {
        loaderLogs.innerHTML += '<br>> Requesting high-resolution DESI tiles...';
    }
    markSurveyLoading('ACQUIRING_TILES');
});

function finishLoadingScreen() {
    const progressBar = document.getElementById('progress-bar');
    const loaderStatus = document.getElementById('loader-status');
    const loaderLogs = document.getElementById('loader-logs');
    const loadingScreen = document.getElementById('loading-screen');

    if (progressBar) progressBar.style.width = '100%';
    if (loaderStatus) loaderStatus.innerText = 'SYSTEM_READY';
    if (loaderLogs) loaderLogs.innerHTML += '<br>> Aladin view ready.';

    setTimeout(() => {
        if (loadingScreen) loadingScreen.classList.add('loader-finished');
    }, 250);
}

function markSurveyLoading(label = 'ACQUIRING_TILES') {
    const captureButton = document.getElementById('capture-button');
    captureReadyAt = Date.now() + TILE_SETTLE_MS;

    if (captureButton) {
        captureButton.disabled = true;
        captureButton.classList.add('is-waiting');
        captureButton.innerText = label;
    }

    if (captureReadyTimer) clearTimeout(captureReadyTimer);
    captureReadyTimer = setTimeout(markSurveyReady, TILE_SETTLE_MS);
}

function markSurveyReady() {
    if (Date.now() < captureReadyAt) {
        captureReadyTimer = setTimeout(markSurveyReady, captureReadyAt - Date.now());
        return;
    }

    const captureButton = document.getElementById('capture-button');
    if (captureButton) {
        captureButton.disabled = false;
        captureButton.classList.remove('is-waiting');
        captureButton.innerText = 'CAPTURE_DATA';
    }
}



function gotoCoordinates() {
    const raInput = document.getElementById('manual-ra').value;
    const decInput = document.getElementById('manual-dec').value;

    if (raInput && decInput && aladin) {
        try {
            const ra = parseFloat(raInput);
            const dec = parseFloat(decInput);

            if (isNaN(ra) || isNaN(dec)) {
                alert("NAVIGATION_ERROR: Invalid coordinate format.");
                return;
            }

            aladin.gotoRaDec(ra, dec);
            markSurveyLoading('ACQUIRING_TILES');

            // Visual feedback: briefly pulse the border
            const group = document.querySelector('.coord-input-group');
            group.style.borderColor = 'var(--accent)';
            setTimeout(() => group.style.borderColor = 'var(--border-ui)', 500);

        } catch (err) {
            console.error("Navigation failed:", err);
        }
    }
}

// Optional: Allow pressing "Enter" in the input fields to trigger navigation
document.addEventListener('DOMContentLoaded', () => {
    const inputs = ['manual-ra', 'manual-dec'];
    inputs.forEach(id => {
        document.getElementById(id).addEventListener('keypress', (e) => {
            if (e.key === 'Enter') gotoCoordinates();
        });
    });
});

    A.init.then(() => {
        aladin = A.aladin('#aladin-lite-div', {
            survey: "CDS/P/DESI-Legacy-Surveys/DR10/color",
            fov: INITIAL_FOV,
            target: "195.163 2.583",
            showZoomControl: false,
            showLayersControl: false,
            showStatus: false,
            showFrame: false,
            showLogo: false,
            showAttribution: false,
            showFullscreenControl: false,
            showSearchControl: false,
            showGotoControl: false,
            fullScreen: false,
            reticleColor: 'transparent',
            cors: 'anonymous'
        });

        const updateTelemetry = () => {
            const raDec = aladin.getRaDec();
            const fov = aladin.getFov();

            if (raDec && fov) {
                document.getElementById('coords-display').textContent =
                    `RA: ${raDec[0].toFixed(5)}° | DEC: ${raDec[1].toFixed(5)}°`;
                document.getElementById('zoom-display').textContent =
                    `FOV: ${fov[0].toFixed(2)}°`;
            }
        };

        aladin.on('positionChanged', () => {
            updateTelemetry();
            markSurveyLoading('ACQUIRING_TILES');
        });
        aladin.on('zoomChanged', () => {
            updateTelemetry();
            markSurveyLoading('ACQUIRING_TILES');
        });

        setInterval(updateTelemetry, 100);
        updateTelemetry();
        setTimeout(() => {
            finishLoadingScreen();
            markSurveyReady();
        }, 500);
    });

    function updateSurvey(id, name, btn) {
        if (aladin) {
            aladin.setImageSurvey(id);
            markSurveyLoading('ACQUIRING_TILES');
            document.getElementById('active-survey-label').innerText = name;
            document.querySelectorAll('.btn-tool').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }
    }

function captureSector() {
    if (Date.now() < captureReadyAt) {
        markSurveyLoading('ACQUIRING_TILES');
        return;
    }

    const aladinCanvas = document.querySelector('#aladin-lite-div canvas');
    const capCanvas = document.getElementById('capture-canvas');
    const ctx = capCanvas.getContext('2d');

    if (aladinCanvas) {
        // Trigger visual shutter effect
        capCanvas.classList.remove('shutter-active');
        void capCanvas.offsetWidth; // Force reflow
        capCanvas.classList.add('shutter-active');

        const sX = (aladinCanvas.width / 2) - 128;
        const sY = (aladinCanvas.height / 2) - 128;
        ctx.clearRect(0, 0, 256, 256);
        ctx.drawImage(aladinCanvas, sX, sY, 256, 256, 0, 0, 256, 256);
    }
}

async function gatherMetadata(ra, dec) {
    try {
        console.log(`[METADATA] Requesting metadata for RA=${ra}, DEC=${dec}`);
        const response = await fetch('http://127.0.0.1:5000/metadata', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                ra: ra,
                dec: dec
            })
        });

        const metadata = await response.json();

        console.log("=== OBSERVATION METADATA ===");
        console.log(`RA: ${ra}°, DEC: ${dec}°`);
        console.log("--- PHOTOMETRIC DATA ---");
        console.log(`Object ID: ${metadata.phot_objid || 'N/A'}`);
        console.log(`Object Type: ${metadata.phot_type || 'N/A'}`);
        console.log(`Magnitudes - u: ${metadata.u_mag || 'N/A'}, g: ${metadata.g_mag || 'N/A'}, r: ${metadata.r_mag || 'N/A'}, i: ${metadata.i_mag || 'N/A'}, z: ${metadata.z_mag || 'N/A'}`);
        console.log(`Petrosian Radius R50 (r-band): ${metadata.petroR50_r || 'N/A'}`);
        console.log(`Petrosian Radius R90 (r-band): ${metadata.petroR90_r || 'N/A'}`);
        console.log("--- SPECTROSCOPIC DATA ---");
        console.log(`Spectroscopic Object ID: ${metadata.specobjid || 'N/A'}`);
        console.log(`Redshift (z): ${metadata.z || 'N/A'}`);
        console.log(`Velocity Dispersion: ${metadata.velDisp || 'N/A'}`);
        console.log(`Class: ${metadata.class || 'N/A'}`);
        console.log(`SubClass: ${metadata.subClass || 'N/A'}`);
        console.log(`Plate: ${metadata.plate || 'N/A'}`);
        console.log(`MJD: ${metadata.mjd || 'N/A'}`);
        console.log(`Fiber ID: ${metadata.fiberID || 'N/A'}`);

        if (metadata.error) {
            console.warn(`[METADATA] Error: ${metadata.error}`);
        }

        console.log("=== END METADATA ===");
        return metadata;

    } catch (error) {
        console.error("[METADATA] Failed to gather metadata:", error);
        return {};
    }
}

function hasMetadataMatch(metadata) {
    if (!metadata || metadata.error) return false;
    return [
        'phot_objid',
        'specobjid',
        'phot_type',
        'class',
        'u_mag',
        'g_mag',
        'r_mag',
        'i_mag',
        'z_mag',
        'z'
    ].some((key) => metadata[key] !== undefined && metadata[key] !== null && metadata[key] !== '');
}

function isGalaxyMetadata(metadata) {
    if (!hasMetadataMatch(metadata)) return false;
    const objectType = metadata.class || metadata.type || metadata.phot_type;
    return String(objectType || '').trim().toUpperCase() === 'GALAXY';
}

function formatMetadataValue(value, digits = 4) {
    if (value === undefined || value === null || value === '') return 'N/A';
    if (typeof value === 'number' && Number.isFinite(value)) return value.toFixed(digits);
    return String(value);
}

function renderMetadataPopup(metadata) {
    if (!isGalaxyMetadata(metadata)) return '';

    return `
        <div class="metadata-found-panel">
            <div class="metadata-found-title">CATALOG_METADATA_FOUND</div>
            <table class="metadata-found-table">
                <tr><td>PHOTO_OBJ</td><td>${formatMetadataValue(metadata.phot_objid, 0)}</td></tr>
                <tr><td>SPEC_OBJ</td><td>${formatMetadataValue(metadata.specobjid, 0)}</td></tr>
                <tr><td>OBJ_TYPE</td><td>${formatMetadataValue(metadata.class || metadata.type || metadata.phot_type, 3)}</td></tr>
                <tr><td>SUBCLASS</td><td>${formatMetadataValue(metadata.subClass, 3)}</td></tr>
                <tr><td>REDSHIFT_Z</td><td>${formatMetadataValue(metadata.z, 5)}</td></tr>
                <tr><td>VEL_DISP</td><td>${formatMetadataValue(metadata.velDisp, 2)}</td></tr>
                <tr><td>PETRO_R50/R90</td><td>${formatMetadataValue(metadata.petroR50_r, 2)} / ${formatMetadataValue(metadata.petroR90_r, 2)}</td></tr>
                <tr><td>MAG_U/G/R/I/Z</td><td>${['u_mag', 'g_mag', 'r_mag', 'i_mag', 'z_mag'].map((key) => formatMetadataValue(metadata[key], 2)).join(' / ')}</td></tr>
                <tr><td>PLATE/MJD/FIBER</td><td>${formatMetadataValue(metadata.plate, 0)} / ${formatMetadataValue(metadata.mjd, 0)} / ${formatMetadataValue(metadata.fiberID, 0)}</td></tr>
            </table>
        </div>
    `;
}

async function predictCapturedObject() {
    const modal = document.getElementById('prediction-modal');
    const box = modal.querySelector('.modal-box');
    const content = document.getElementById('modal-content');
    const footer = document.getElementById('modal-footer-actions');
    const correctionUI = document.getElementById('correction-ui');

    // Reset UI state
    correctionUI.style.display = 'none';
    box.classList.remove('modal-retract');
    box.classList.add('modal-deploy');
    modal.style.display = 'flex';

    content.innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <div style="display: inline-block; width: 20px; height: 20px; border: 2px solid var(--border-ui); border-radius: 50%; border-top-color: var(--accent); animation: spin 1s linear infinite; margin-bottom: 10px;"></div>
            <br>STATUS: PROCESSING...<br>
            <span style="color: var(--accent);">INITIALIZING PYTORCH KERNEL...</span>
        </div>
    `;
    footer.innerHTML = `<button class="btn-close" onclick="closeModal()">CANCEL</button>`;

    try {
        const capCanvas = document.getElementById('capture-canvas');
        const imageData = capCanvas.toDataURL('image/jpeg');

        // Get current coordinates from Aladin
        const coords = aladin ? aladin.getRaDec() : [0, 0];
        const surveyLabel = document.getElementById('active-survey-label').textContent;

        const fov = aladin ? aladin.getFov()[0] : 0;

        const response = await fetch('http://127.0.0.1:5000/predict', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                image: imageData,
                ra: coords[0] || 0,
                dec: coords[1] || 0,
                fov: fov || 0,
                survey: surveyLabel
            })
        });

        const data = await response.json();

        // Store for potential correction
        window.lastPrediction = data;
        window.currentDiscovery = {
            img: imageData,
            ra: coords[0] || 0,
            dec: coords[1] || 0,
            prediction: data.prediction,
            confidence: data.confidence,
            observation_id: data.observation_id,
            metadata: data.metadata || {}
        };

        setTimeout(() => {
            // Build class probabilities table
            let probabilitiesHTML = '';
            if (data.class_probabilities) {
                probabilitiesHTML = `
                    <div style="margin-top: 15px; padding: 10px; border: 1px solid var(--border-ui); background: rgba(0,0,0,0.3); font-size: 9px;">
                        <div style="color: var(--dim); margin-bottom: 8px; font-family: var(--font-mono);">CLASS_PROBABILITIES:</div>
                        <table style="width: 100%; border-collapse: collapse;">
                `;
                for (const [className, probability] of Object.entries(data.class_probabilities)) {
                    const barWidth = Math.round(probability / 100 * 100);
                    probabilitiesHTML += `
                        <tr style="height: 22px;">
                            <td style="padding: 2px 5px; text-align: left; white-space: nowrap;">${className}</td>
                            <td style="padding: 2px 5px; width: 100%; position: relative;">
                                <div style="background: rgba(0, 212, 255, 0.2); height: 16px; border: 1px solid var(--accent); position: relative;">
                                    <div style="background: var(--accent); height: 100%; width: ${barWidth}%; transition: width 0.3s;"></div>
                                    <span style="position: absolute; right: 3px; top: 0; font-size: 8px; color: #00f95b; font-weight: bold;">${probability}%</span>
                                </div>
                            </td>
                        </tr>
                    `;
                }
                probabilitiesHTML += `
                        </table>
                    </div>
                `;
            }
            
            content.innerHTML = `
                IDENTIFICATION: <span class="prediction-value">${data.prediction.toUpperCase()}</span><br>
                CONFIDENCE: <span class="prediction-value">${data.confidence}%</span><br>
                OBSERVATION_ID: <span class="prediction-value">${data.observation_id}</span><br>
                ${probabilitiesHTML}
                ${renderMetadataPopup(data.metadata)}
                <span style="color: #6b7280; font-size: 9px;">VALIDATE_NEURAL_LOGIC?</span>
            `;

            // Add Confirm/Override buttons
            footer.innerHTML = `
                <button class="btn-tool" onclick="openReport()">VIEW_METADATA</button>
                <button class="btn-tool btn-override" onclick="showCorrectionUI()">OVERRIDE</button>
                <button class="btn-tool btn-confirm" onclick="confirmPrediction()">CONFIRM</button>
            `;
        }, 600);

    } catch (error) {
        content.innerHTML = `<span style="color: #ef4444;">ERROR: NO_RESPONSE</span>`;
    }
}

function showCorrectionUI() {
    document.getElementById('correction-ui').style.display = 'block';
    document.getElementById('modal-footer-actions').innerHTML = `<button class="btn-close" onclick="closeModal()">ABORT</button>`;
}

async function confirmPrediction() {
    const content = document.getElementById('modal-content');
    const data = window.lastPrediction;
    if (!data || !data.observation_id) {
        content.innerHTML = `<span style="color: #ef4444;">ERROR: MISSING_OBSERVATION_ID</span>`;
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/api/observation/${encodeURIComponent(data.observation_id)}/classify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                predicted_class: data.prediction,
                confidence: data.confidence / 100,
                model_version: data.model_version,
                is_manual: false
            })
        });

        if (!response.ok) {
            const result = await response.json();
            content.innerHTML = `<span style="color: #ef4444;">ERROR: ${result.error || 'CONFIRM_FAILED'}</span>`;
            return;
        }

        content.innerHTML = `<span style="color: #4ade80;">LOGGED: POSITIVE_VERIFICATION</span><br><span style="font-size:9px">Classification saved to archive.</span>`;
        setTimeout(closeModal, 1000);
    } catch (err) {
        console.error('Confirm failed:', err);
        content.innerHTML = `<span style="color: #ef4444;">ERROR: NETWORK_FAILURE</span>`;
    }
}

async function submitCorrection() {
    const newClass = document.getElementById('manual-class').value;
    const content = document.getElementById('modal-content');
    const data = window.lastPrediction;

    if (!data || !data.observation_id) {
        content.innerHTML = `<span style="color: #ef4444;">ERROR: MISSING_OBSERVATION_ID</span>`;
        return;
    }

    try {
        const response = await fetch(`http://127.0.0.1:5000/api/observation/${encodeURIComponent(data.observation_id)}/classify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                predicted_class: newClass,
                confidence: 1.0,
                model_version: data.model_version,
                is_manual: true,
                original_prediction: data.prediction,
                comments: 'User override'
            })
        });

        if (!response.ok) {
            const result = await response.json();
            content.innerHTML = `<span style="color: #ef4444;">ERROR: ${result.error || 'OVERRIDE_FAILED'}</span>`;
            return;
        }

        content.innerHTML = `<span style="color: #f87171;">LOGGED: MANUAL_OVERRIDE</span><br>
                             <span style="font-size:9px">Corrected to: ${newClass.toUpperCase()}</span>`;
        setTimeout(closeModal, 1500);
    } catch (err) {
        console.error('Override failed:', err);
        content.innerHTML = `<span style="color: #ef4444;">ERROR: NETWORK_FAILURE</span>`;
    }
}






async function openReport() {
    const d = window.currentDiscovery;
    const reportUI = document.getElementById('discovery-report');
    if (!d) return;

    // Smooth transition in
    reportUI.style.display = 'block';
    setTimeout(() => reportUI.classList.add('visible'), 10);

    const ra = parseFloat(d.ra);
    const dec = parseFloat(d.dec);

    document.getElementById('report-img').src = d.img;
    document.getElementById('res-class').innerText = d.prediction;
    document.getElementById('res-conf').innerText = d.confidence + "%";
    document.getElementById('res-coords').innerText = `${ra.toFixed(5)}, ${dec.toFixed(5)}`;
    document.getElementById('report-timestamp').innerText = new Date().toUTCString();

    const briefBox = document.getElementById('report-brief');
    const idField = document.getElementById('res-simbad-id');
    idField.innerText = "QUERYING ARCHIVES...";

    let externalData = { info: "No catalog match found within 5 arcsec." };
    const capturedMetadata = d.metadata || {};

    if (isGalaxyMetadata(capturedMetadata)) {
        idField.innerText = capturedMetadata.phot_objid || capturedMetadata.specobjid || "SDSS DR19";
        document.getElementById('res-simbad-type').innerText = capturedMetadata.class || capturedMetadata.type || capturedMetadata.phot_type || "OBJ";
        document.getElementById('res-simbad-mag').innerText = capturedMetadata.r_mag ? Number(capturedMetadata.r_mag).toFixed(2) : "N/A";
        document.getElementById('res-simbad-z').innerText = capturedMetadata.z ? Number(capturedMetadata.z).toFixed(5) : "N/A";
        externalData.info = `SDSS Match: type ${capturedMetadata.class || capturedMetadata.type || capturedMetadata.phot_type || "OBJ"}, r_mag: ${formatMetadataValue(capturedMetadata.r_mag, 2)}, z: ${formatMetadataValue(capturedMetadata.z, 5)}`;
    }

    try {
        const url = `http://127.0.0.1:5000/legacy?ra=${ra}&dec=${dec}&radius=0.01`;
        const res = await fetch(url);
        const data = await res.json();

        if (!isGalaxyMetadata(capturedMetadata) && data && data.sources && data.sources.length > 0) {
            // Sorting by distance to get the absolute closest object
            const best = data.sources.sort((a, b) => {
                const distA = Math.hypot(a.ra - ra, a.dec - dec);
                const distB = Math.hypot(b.ra - ra, b.dec - dec);
                return distA - distB;
            })[0];

            const mag_r = best.flux_r > 0 ? (-2.5 * Math.log10(best.flux_r) + 22.5).toFixed(2) : "N/A";
            const g_r = (best.flux_g > 0 && best.flux_r > 0)
                        ? ((-2.5 * Math.log10(best.flux_g) + 22.5) - (-2.5 * Math.log10(best.flux_r) + 22.5)).toFixed(2)
                        : "N/A";

            idField.innerText = "LEGACY DR10";
            document.getElementById('res-simbad-type').innerText = best.type || "OBJ";
            document.getElementById('res-simbad-mag').innerText = mag_r;
            document.getElementById('res-simbad-z').innerText = `g-r: ${g_r}`;
            externalData.info = `Legacy Match: ${best.type}, mag_r: ${mag_r}, g-r: ${g_r}`;
        } else if (!isGalaxyMetadata(capturedMetadata)) {
            // --- STEP 2: Fallback to SIMBAD TAP (Global) ---
            const adql = `SELECT TOP 1 main_id,ot_type,mag_v FROM basic WHERE CONTAINS(POINT('ICRS',ra,dec),CIRCLE('ICRS',${ra},${dec},0.002))=1`;
            const simbadUrl = `https://simbad.u-strasbg.fr/simbad/sim-tap/sync?request=doQuery&lang=adql&format=json&query=${encodeURIComponent(adql)}`;

            const sRes = await fetch(simbadUrl).then(r => r.json());
            if (sRes.data && sRes.data.length > 0) {
                const s = sRes.data[0];
                idField.innerText = s[0];
                document.getElementById('res-simbad-type').innerText = s[1];
                document.getElementById('res-simbad-mag').innerText = s[2] || "N/A";
                externalData.info = `SIMBAD Match: ${s[0]}, Type: ${s[1]}`;
            } else {
                idField.innerText = "NO NEIGHBOR FOUND";
            }
        }
    } catch (e) {
        console.error("Metadata Fetch Failed", e);
        idField.innerText = "OFFLINE";
    }

    // --- STEP 3: Chat Synthesis ---
    briefBox.innerText = "SYNTHESIZING...";
    try {
        const chatPrompt = `Summarize: Object at ${ra}, ${dec} predicted as ${d.prediction}. Catalog Data: ${externalData.info}`;
        const chatRes = await fetch('http://127.0.0.1:5000/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: chatPrompt })
        });
        const reader = chatRes.body.getReader();
        briefBox.innerText = "";
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;
            briefBox.innerText += new TextDecoder().decode(value);
        }
    } catch (e) { briefBox.innerText = "AI Synthesis failed. View raw metadata above."; }
}

function closeReport() {

    document.getElementById('discovery-report').style.display = 'none';

}

function closeModal() {
    const modal = document.getElementById('prediction-modal');
    const box = modal.querySelector('.modal-box');

    if (box) {
        box.classList.remove('modal-deploy');
        box.classList.add('modal-retract');
        setTimeout(() => {
            modal.style.display = 'none';
            box.classList.remove('modal-retract');
        }, 300);
    } else {
        modal.style.display = 'none';
    }
}