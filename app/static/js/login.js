
window.onload = function () {
    generateCaptcha("captchaCode");
    generateCaptcha("captchaCode2");
};


async function submitFormVerify(event) {
    event.preventDefault();  // Prevent the default form submission
    showLoading('verify-button');
    const salt = getCookie("Session-SALT");  // Assuming the salt cookie is named "salt"
    if (!salt) {
        console.error("Salt not found in cookies.");
        return;
    }
    const form = document.getElementById("otp-form");
    const formData = new FormData(form);
    const formDataJson = Object.fromEntries(formData.entries())

    const Loginform = document.getElementById("login-form");
    const LoginformData = new FormData(Loginform);
    const LoginformDataJson = Object.fromEntries(LoginformData.entries())
    formDataJson["employee_id"] = LoginformDataJson["employee_id"]
    const data = JSON.stringify(formDataJson);
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
            console.log("successfull");
            window.location.href = "../researchrepository/home";
        } else {
            // Handle errors, if any (e.g., show an error message)
            const data = await response.json();
            showAlert(data.message);
            console.error("Form submission failed.");
        }
    } catch (error) {
        showAlert(error);
        console.error("An error occurred:", error);
    }

    stopLoading('verify-button');
}

async function submitForm(event) {
    event.preventDefault();  // Prevent the default form submission

    showLoading('login-button');

    const salt = getCookie("Session-SALT");  // Assuming the salt cookie is named "salt"
    if (!salt) {
        console.error("Salt not found in cookies.");
        return;
    }
    const form = document.getElementById("login-form");
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
            toggleForms();
            showAlert('OTP sent', true);
        } else {
            // Handle errors, if any (e.g., show an error message)
            const data = await response.json();
            showAlert(data.message);
            console.error("Form submission failed.");
        }
    } catch (error) {
        showAlert(error);
        console.error("An error occurred:", error);
    }
    stopLoading('login-button');
}

function toggleForms() {
    document.getElementById("otp-form").style.display = "block";
    document.getElementById("login-form").style.display = "none";
}
