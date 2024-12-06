
async function uploadrisFile() {
    const form = document.getElementById('uploadForm');
    const formData = new FormData(form);

    try {
        const response = await fetch("../researchrepository/api/article/upload_ris", {
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
        const response = await fetch("../researchrepository/api/article/upload_nbib", {
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

// Function to show the alert box with a custom message and success/failure status
function showAlert(message, isSuccess) {
    const alertBox = document.getElementById('customAlert');
    const alertMessage = document.getElementById('alertMessage');

    alertMessage.textContent = message; // Set the alert message

    // Toggle class based on success or failure
    if (isSuccess) {
        alertBox.classList.add('success'); // Add success class for green color
        alertBox.classList.remove('failure'); // Remove failure class if present
    } else {
        alertBox.classList.remove('success'); // Remove success class if present
        alertBox.classList.add('failure'); // Add failure class for red color
    }

    alertBox.style.display = 'block'; // Show the alert box
}

// Function to close the alert box
function closeAlert() {
    const alertBox = document.getElementById('customAlert');
    alertBox.style.display = 'none'; // Hide the alert box
}



async function submitForm(event) {
    event.preventDefault();  // Prevent the default form submission
    const salt = getCookie("Session-SALT");  // Assuming the salt cookie is named "salt"
    if (!salt) {
        console.error("Salt not found in cookies.");
        return;
    }
    const form = document.getElementById("pubmed-form");
    const formData = new FormData(form);
    const formDataJson = Object.fromEntries(formData.entries())

    const data = JSON.stringify(formDataJson);
    console.log(data)
    const encodeFunction = await cipher(salt);
    const encryptedData = encodeFunction(data);

    try {
        // Send data to the server using fetch API
        const response = await fetch(form.action, {
            method: form.method,
            headers: {
                'Content-Type': 'application/json',  // Ensure JSON is being sent
            },
            body: JSON.stringify({ data: encryptedData })
        });

        // Check if the response is successful
        if (response.ok) {
            // Call toggleForms if the response is successful
            showAlert('Pubmed data added successfully',true);
        } else {
            // Handle errors, if any (e.g., show an error message)
            console.error("Form submission failed.");
        }
    } catch (error) {
        console.error("An error occurred:", error);
    }
}



