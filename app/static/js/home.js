// Helper: Show Modal
function showModal(title, summary, data) {
    document.getElementById("modalTitle").textContent = title;
    document.getElementById("modalSummary").textContent = summary;

    const modalContent = document.getElementById("modalContent");
    modalContent.innerHTML = ""; // Clear previous content

    const addedCount = data.added_articles || 0;
    const duplicateCount = Object.values(data.duplicate_articles || {}).flat().length;
    const skippedCount = data.skipped_articles || 0;

    const summarySection = document.createElement("div");
    summarySection.classList.add("p-4", "space-y-3", "bg-gray-100", "rounded-lg");

    summarySection.innerHTML = `
        <p class="text-gray-800 text-lg">
            <strong>Upload Summary:</strong>
        </p>
        <ul class="list-disc pl-5 space-y-1">
            <li class="text-green-700 font-medium">Added Articles: ${addedCount}</li>
            <li class="text-yellow-700 font-medium">Duplicate Articles: ${duplicateCount}</li>
            <li class="text-red-700 font-medium">Skipped Articles: ${skippedCount}</li>
        </ul>
    `;

    modalContent.appendChild(summarySection);

    // Show the modal
    document.getElementById("resultModal").classList.remove("hidden");
}

// Helper: Close Modal
function closeModal() {
    document.getElementById("resultModal").classList.add("hidden");
}

// Upload .ris File
async function uploadrisFile() {
    const form = document.getElementById("uploadForm");
    const formData = new FormData(form);
    const button = form.querySelector("button");

    showLoading('upload_ris_btn');

    try {
        const response = await fetch("../api/article/upload_ris", {
            method: "POST",
            body: formData,
        });

        stopLoading('upload_ris_btn');

        if (response.ok) {
            const result = await response.json();
            showModal(
                "Upload Successful",
                `File uploaded: ${result.filename}`,
                result
            );
        } else {
            const error = await response.json();
            showAlert(`Error: ${error.error}`);
        }
    } catch (error) {
        console.error("Upload error:", error);
        showAlert("An error occurred while uploading the file.");
        stopLoading('upload_ris_btn');
    }
}

// Upload .nbib File
async function uploadnbibFile() {
    const form = document.getElementById("uploadForm-nbib");
    const formData = new FormData(form);
    const button = form.querySelector("button");

    showLoading('upload_nib_btn');

    try {
        const response = await fetch("../api/article/upload_nbib", {
            method: "POST",
            body: formData,
        });
        stopLoading('upload_nib_btn');


        if (response.ok) {
            const result = await response.json();
            showModal(
                "Upload Successful",
                `File uploaded: ${result.filename}`,
                result
            );
        } else {
            const error = await response.json();
            showAlert(`Error: ${error.error}`);
        }
    } catch (error) {
        console.error("Upload error:", error);
        showAlert("An error occurred while uploading the file.");
        stopLoading('upload_nib_btn');
    }
}

// Submit PubMed Form
async function submitForm(event) {
    event.preventDefault();
    const form = document.getElementById("pubmed-form");
    const formData = new FormData(form);
    const salt = getCookie("Session-SALT");
    showLoading('upload_pubmed_btn');

    if (!salt) {
        console.error("Salt not found in cookies.");
        showAlert("Error: Session expired. Please log in again.");
        return;
    }

    const formDataJson = Object.fromEntries(formData.entries());
    const data = JSON.stringify(formDataJson);
    const encodeFunction = await cipher(salt);
    const encryptedData = encodeFunction(data);

    try {
        const response = await fetch(form.action, {
            method: form.method,
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ data: encryptedData }),
        });
        stopLoading('upload_pubmed_btn');

        if (response.ok) {
            showAlert("PubMed data added successfully", true);
        } else {
            showAlert("Error: Unable to add PubMed data.");
        }
    } catch (error) {
        console.error("An error occurred:", error);
        showAlert("An error occurred while submitting the PubMed form.");
        stopLoading('upload_pubmed_btn');
    }
}
