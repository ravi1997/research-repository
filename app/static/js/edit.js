let draggedRow = null;

function onDragStart(event) {
    draggedRow = event.target;
    event.dataTransfer.effectAllowed = "move";
    draggedRow.style.opacity = "0.5";
}

function onDragOver(event) {
    event.preventDefault();
    event.dataTransfer.dropEffect = "move";
    const targetRow = event.target.closest("tr");
    if (targetRow && targetRow !== draggedRow) {
        const tbody = targetRow.parentNode;
        const rows = Array.from(tbody.children);
        const draggedIndex = rows.indexOf(draggedRow);
        const targetIndex = rows.indexOf(targetRow);
        tbody.insertBefore(draggedRow, draggedIndex < targetIndex ? targetRow.nextSibling : targetRow);
    }
}

function onDrop(event) {
    event.preventDefault();
    if (draggedRow) {
        draggedRow.style.opacity = "1";
        draggedRow = null;
    }
}

// Helper function for removing a row
function removeRow(button) {
    button.closest('tr').remove();
}

// Helper function to add a row to any table with dynamic indexing
function addRow(tableId, fields) {
    const table = document.getElementById(tableId);
    const tbody = table.querySelector('tbody');
    const index = tbody.rows.length + 1;
    const newRow = tbody.insertRow();

    // Set drag and drop attributes
    newRow.setAttribute("draggable", "true");
    newRow.setAttribute("ondragstart", "onDragStart(event)");
    newRow.setAttribute("ondragover", "onDragOver(event)");
    newRow.setAttribute("ondrop", "onDrop(event)");

    fields.forEach((field, idx) => {
        if(field=='id')
            return;
        const cell = newRow.insertCell();
        cell.classList.add("px-4");
        cell.classList.add("py-2");
        if (field === 'remove') {
            cell.innerHTML = `<button type="button" class="btn btn-sm btn-danger" onclick="removeRow(this)">Remove</button>`;
        } else {
            const name = `${field}[${index}]`;
            cell.innerHTML = `<input type="text" name="${name}" value="" required class="input input-bordered w-full">`;
        }
    });
}

// Event listeners for adding authors, keywords, and links
document.getElementById('add-author-btn').addEventListener('click', () => {
    addRow('authors-table', ['id', 'fullName', 'affiliation', 'abbreviation', 'remove']);
});

document.getElementById('add-keyword-btn').addEventListener('click', () => {
    addRow('keywords-table', ['id', 'keyword', 'remove']);
});

document.getElementById('add-link-btn').addEventListener('click', () => {
    addRow('links-table', ['id', 'link', 'remove']);
});

function showSuccessModal() {
    const modal = document.getElementById('successModal');
    modal.classList.remove('hidden');
}

// Close the modal
function closeModal() {
    window.location.href = "../"+article_uuid;
}



// Collect form data, including dynamic rows (authors, keywords, links)
async function submitForm(event) {
    event.preventDefault();
    showLoading('submit-btn');

    const salt = getCookie("Session-SALT");
    if (!salt) {
        console.error("Salt not found in cookies.");
        return;
    }

    const form = document.getElementById("edit-form");
    const formData = new FormData(form);
    const formDataJson = Object.fromEntries(formData.entries());

    const tables = ['authors', 'keywords', 'links'];

    tables.forEach(tableId => {
        const table = document.getElementById(`${tableId}-table`);
        const rows = Array.from(table.querySelectorAll("tr"));
        const data = [];

        rows.forEach((row, index) => {
            const inputs = row.querySelectorAll("input");
            const rowData = { sequence_number: index };

            inputs.forEach(input => {
                const match = input.name.match(new RegExp(`${tableId}\\[(\\d+)\\]\\[(\\w+)\\]`));
                if (match) {
                    rowData[match[2]] = input.value;
                    delete formDataJson[input.name]; // Remove from the base formDataJson
                }
            });

            if (Object.keys(rowData).length > 1) {
                data.push(rowData);
            }
        });

        formDataJson[tableId] = data;
    });

    formDataJson['uuid'] = article_uuid;

    const data = JSON.stringify(formDataJson);
    console.log(data);
    const encodeFunction = await cipher(salt);
    const encryptedData = encodeFunction(data);

    try {
        const response = await fetch(form.action, {
            method: form.method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ data: encryptedData })
        });
        showLoading('submit-btn');

        if (response.ok) {
            showSuccessModal();
            console.log("Successful");
        } else {
            const data = await response.json();
            showAlert(data["message"]);
            console.error("Form submission failed.");
        }
    } catch (error) {
        showLoading('submit-btn');
        showAlert(error);

        console.error("An error occurred:", error);
    }
}
