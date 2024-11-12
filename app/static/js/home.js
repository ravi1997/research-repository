
window.onload = function () {
    generateCaptcha("captchaCode");
};

async function uploadrisFile() {
    const form = document.getElementById('uploadForm');
    const formData = new FormData(form);

    try {
        const response = await fetch("../researchrepository/api/public/upload_ris", {
            method: "POST",
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            document.getElementById("message").innerText = "File uploaded successfully: " + result.filename;
        } else {
            const error = await response.json();
            document.getElementById("message").innerText = "Error: " + error.error;
        }
    } catch (error) {
        console.error("Upload error:", error);
        document.getElementById("message").innerText = "An error occurred while uploading the file.";
    }
}

async function uploadnbibFile() {
    const form = document.getElementById('uploadForm-nbib');
    const formData = new FormData(form);

    try {
        const response = await fetch("../researchrepository/api/public/upload_nbib", {
            method: "POST",
            body: formData
        });

        if (response.ok) {
            const result = await response.json();
            document.getElementById("message1").innerText = "File uploaded successfully: " + result.filename;
        } else {
            const error = await response.json();
            document.getElementById("message1").innerText = "Error: " + error.error;
        }
    } catch (error) {
        console.error("Upload error:", error);
        document.getElementById("message1").innerText = "An error occurred while uploading the file.";
    }
}

// Function to show the alert box with a custom message
function showAlert(message) {
    const alertBox = document.getElementById("customAlert");
    const alertMessage = document.getElementById("alertMessage");
    alertMessage.innerText = message;
    alertBox.style.display = "block";

    // Hide the alert automatically after 3 seconds
    setTimeout(closeAlert, 3000);
}

// Function to close the alert box
function closeAlert() {
    document.getElementById("customAlert").style.display = "none";
}




async function logout(){
    try {
        const response = await fetch("../researchrepository/api/auth/logout", {
            method: "GET",
        });

        if (response.ok) {
            window.location.href = "../researchrepository/login";
        } else {
            const error = await response.json()["message"];
            showAlert(error);
        }
    } catch (error) {
        console.error(error);
        showAlert(error);
    }
}