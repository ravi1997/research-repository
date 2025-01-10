function generateCaptcha(id) {
    const captcha = Math.random().toString(36).substring(2, 8).toUpperCase();
    document.getElementById(id).textContent = captcha;
    currentCaptcha = captcha;
}


async function hashSalt(salt) {
    const encoder = new TextEncoder();
    const data = encoder.encode(salt);
    const hashBuffer = await crypto.subtle.digest('SHA-256', data);
    const hashArray = Array.from(new Uint8Array(hashBuffer));
    return hashArray.map(byte => byte.toString(16).padStart(2, '0')).join('');
}

async function cipher(salt) {
    const hashedSalt = await hashSalt(salt);
    const textToChars = text => text.split('').map(c => c.charCodeAt(0));
    const byteHex = n => ("0" + Number(n).toString(16)).substr(-2);
    const applySaltToChar = code => textToChars(hashedSalt).reduce((a, b) => a ^ b, code);

    return text => text.split('')
        .map(textToChars)
        .map(applySaltToChar)
        .map(byteHex)
        .join('');
}


function getCookie(name) {
    const nameEQ = name + "=";
    const ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i];
        while (c.charAt(0) == ' ') c = c.substring(1, c.length);
        if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length, c.length);
    }
    return null;
}


async function logout() {
    try {
        const response = await fetch("/api/auth/logout", {
            method: "GET",
        });

        if (response.ok) {
            window.location.href = "/login";
        } else {
            const error = await response.json()["message"];
            showAlert(error, false);
        }
    } catch (error) {
        console.error(error);
        showAlert(error, false);
    }
}


// Function to show the alert box with a custom message and success/failure status
function showAlert(message, isSuccess) {
    const alertBox = document.getElementById('customAlert');
    const alertMessage = document.getElementById('alertMessage');

    alertMessage.textContent = message; // Set the alert message

    // Toggle class based on success or failure
    if (isSuccess) {
        alertBox.classList.add('bg-green-100'); // Add success class for green color
        alertBox.classList.add('text-green-800'); // Add success class for green color
             
        alertBox.classList.remove('hidden'); // Remove failure class if present
        alertBox.classList.remove('bg-red-100'); // Remove failure class if present
        alertBox.classList.remove('text-red-800'); // Remove failure class if present
    } else {
        alertBox.classList.remove('bg-green-100'); // Add success class for green color
        alertBox.classList.remove('text-green-800'); // Add success class for green color

        alertBox.classList.add('hidden'); // Remove failure class if present
        alertBox.classList.add('bg-red-100'); // Remove failure class if present
        alertBox.classList.add('text-red-800'); // Remove failure class if present
    }

    alertBox.style.display = 'block'; // Show the alert box
}

// Function to close the alert box
function closeAlert() {
    const alertBox = document.getElementById('customAlert');
    alertBox.style.display = 'none'; // Hide the alert box
}

function showLoading(buttonId) {
    const button = document.getElementById(buttonId);
    const spinner = button.querySelector(".loading-spinner");
    const buttonText = button.querySelector(".button-text");

    buttonText.style.display = "none"; // Hide button text
    spinner.style.display = "inline-block"; // Show spinner
    spinner.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="feather feather-loader"><circle cx="12" cy="12" r="10"></circle><path d="M12 2v4"></path></svg>`; // Add spinner SVG
    button.disabled = true; // Disable the button
}

function stopLoading(buttonId) {
    const button = document.getElementById(buttonId);
    const spinner = button.querySelector(".loading-spinner");
    const buttonText = button.querySelector(".button-text");

    buttonText.style.display = "inline"; // Show button text
    spinner.style.display = "none"; // Hide spinner
    spinner.innerHTML = ""; // Remove spinner content
    button.disabled = false; // Re-enable the button
}