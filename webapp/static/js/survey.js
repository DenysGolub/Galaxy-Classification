window.addEventListener('load', () => {
    const progressBar = document.getElementById('progress-bar');
    const loaderStatus = document.getElementById('loader-status');
    const loaderLogs = document.getElementById('loader-logs');
    const loadingScreen = document.getElementById('loading-screen');

    const logs = [
        "> Syncing with DESI DR10 archives...",
        "> Calibrating optical sensors...",
        "> Neural engine online.",
        "> Handshake complete."
    ];

    let progress = 0;
    let logIndex = 0;

    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress > 100) progress = 100;
        
        progressBar.style.width = progress + "%";

        if (progress > 25 && logIndex === 0) { addLog(logs[0]); logIndex++; }
        if (progress > 50 && logIndex === 1) { addLog(logs[1]); logIndex++; }
        if (progress > 75 && logIndex === 2) { addLog(logs[2]); logIndex++; }

        if (progress === 100) {
            clearInterval(interval);
            loaderStatus.innerText = "SYSTEM_READY";
            addLog(logs[3]);
            
            // Fade out screen
            setTimeout(() => {
                loadingScreen.classList.add('loader-finished');
            }, 500);
        }
    }, 150);

    function addLog(msg) {
        loaderLogs.innerHTML += `<br>${msg}`;
    }
});



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

    let aladin;
    
    A.init.then(() => {
        aladin = A.aladin('#aladin-lite-div', {
            survey: "CDS/P/DESI-Legacy-Surveys/DR10/color",
            fov: 1.5, 
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

        aladin.on('positionChanged', updateTelemetry);
        aladin.on('zoomChanged', updateTelemetry);
        
        setInterval(updateTelemetry, 100);
    });

    function updateSurvey(id, name, btn) {
        if (aladin) {
            aladin.setImageSurvey(id);
            document.getElementById('active-survey-label').innerText = name;
            document.querySelectorAll('.btn-tool').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
        }
    }

function captureSector() {
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

        setTimeout(() => {
            content.innerHTML = `
                IDENTIFICATION: <span class="prediction-value">${data.prediction.toUpperCase()}</span><br>
                CONFIDENCE: <span class="prediction-value">${data.confidence}%</span><br>
                OBSERVATION_ID: <span class="prediction-value">${data.observation_id}</span><br>
                <span style="color: #6b7280; font-size: 9px;">VALIDATE_NEURAL_LOGIC?</span>
            `;

            // Add Confirm/Override buttons
            footer.innerHTML = `
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
                model_version: 'best_0.8200.pth',
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
                model_version: 'best_0.8200.pth',
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

function closeModal() {
    const modal = document.getElementById('prediction-modal');
    const box = modal.querySelector('.modal-box');

    box.classList.remove('modal-deploy');
    box.classList.add('modal-retract');

    setTimeout(() => {
        modal.style.display = 'none';
        box.classList.remove('modal-retract');
    }, 300);
}

function closeModal() {
    const modal = document.getElementById('prediction-modal');
    const box = modal.querySelector('.modal-box');

    box.classList.remove('modal-deploy');
    box.classList.add('modal-retract');

    setTimeout(() => {
        modal.style.display = 'none';
        box.classList.remove('modal-retract');
    }, 300);
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

    try {
        const url = `http://127.0.0.1:5000/legacy?ra=${ra}&dec=${dec}&radius=0.01`;
        const res = await fetch(url);
        const data = await res.json();

        if (data && data.sources && data.sources.length > 0) {
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
        } else {
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

    document.getElementById('prediction-modal').style.display = 'none';

}
