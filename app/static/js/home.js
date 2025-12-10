// Helper: Show Modal
function showModal(title, summary, data) {
    document.getElementById("modalTitle").textContent = title;
    document.getElementById("modalSummary").textContent = summary;

    const modalContent = document.getElementById("modalContent");
    modalContent.innerHTML = ""; // Clear previous content

    const summaryHtml = `
    <div class="p-4 bg-gray-100 rounded-lg">
      <p><strong>Upload Summary:</strong></p>
      <ul>
        <li class="text-green-600">Added Articles: ${data.added_articles || 0}</li>
        <li class="text-yellow-600">Duplicate Articles: ${Object.values(data.duplicate_articles || {}).flat().length}</li>
        <li class="text-red-600">Skipped Articles: ${data.skipped_articles || 0}</li>
      </ul>
    </div>`;
    modalContent.innerHTML = summaryHtml;

    document.getElementById("resultModal").classList.remove("hidden");
}


function showProgressModal(title, summary) {
    document.getElementById("modalTitle").textContent = title;
    document.getElementById("modalSummary").textContent = summary;

    const modalContent = document.getElementById("modalContent");
    modalContent.innerHTML = ""; // Clear previous content

    const summaryHtml = `
    <div class="p-4 bg-gray-100 rounded-lg">
      <p><strong>Processing request, please wait.</strong></p>
    </div>`;
    modalContent.innerHTML = summaryHtml;

    document.getElementById("resultModal").classList.remove("hidden");
}


// Helper: Close Modal
function closeModal() {
    document.getElementById("resultModal").classList.add("hidden");
}

// Helper: Show Alert
function showAlert(message, isSuccess = false) {
    const alertBox = document.getElementById("customAlert");
    const alertMessage = document.getElementById("alertMessage");

    alertBox.classList.remove("hidden", isSuccess ? "bg-red-500" : "bg-green-500");
    alertBox.classList.add(isSuccess ? "bg-green-500" : "bg-red-500");
    alertMessage.textContent = message;

    setTimeout(() => alertBox.classList.add("hidden"), 3000);
}

// File Upload Functionality
async function uploadFile(fileType) {
    const form = fileType === "ris" ? document.getElementById("uploadFormRIS") : document.getElementById("uploadFormNBIB");
    const formData = new FormData(form);
    const buttonId = fileType === "ris" ? "uploadRISButton" : "uploadNBIBButton";

    const button = document.getElementById(buttonId);
    button.disabled = true;

    try {
        showProgressModal("Uploading and Processing file", `File uploading`)
        const response = await fetch(`../api/article/upload_${fileType}`, {
            method: "POST",
            body: formData,
        });
        
        if (response.ok) {
            const result = await response.json();
            document.getElementById("resultModal").classList.add("hidden");
            showModal("Upload Successful", `File uploaded: ${result.filename}`, result);
        } else {
            const error = await response.json();
            document.getElementById("resultModal").classList.add("hidden");
            showAlert(`Error: ${error.error}`);
        }
    } catch (error) {
        console.error("Error uploading file:", error);
        document.getElementById("resultModal").classList.add("hidden");
        showAlert("An error occurred while uploading the file.");
    } finally {
        button.disabled = false;
    }
}

// PubMed Fetch Functionality
async function submitPubMed(event) {
    event.preventDefault();

    const pubmedID = document.getElementById("pubmedID").value;
    const button = document.getElementById("fetchPubMedButton");
    button.disabled = true;
    showProgressModal("Uploading and Processing request", ``)

    try {
        const response = await fetch(`../api/article/pubmedFetch`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pmid: pubmedID }),
        });

        if (response.ok) {
            const result = await response.json();
            document.getElementById("resultModal").classList.add("hidden");
            showAlert("PubMed data added successfully", true);
        } else {
            const error = await response.json();
            document.getElementById("resultModal").classList.add("hidden");
            showAlert(`Error: ${error.message}`);
        }
    } catch (error) {
        console.error("Error fetching PubMed data:", error);
        document.getElementById("resultModal").classList.add("hidden");
        showAlert("An error occurred while fetching PubMed data.");
    } finally {
        button.disabled = false;
    }
}
