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



