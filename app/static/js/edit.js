let draggedRow = null;

function onDragStart(event) {
    draggedRow = event.target;
    event.dataTransfer.effectAllowed = "move";
    event.target.style.opacity = "0.5";
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
        if (draggedIndex < targetIndex) {
            tbody.insertBefore(draggedRow, targetRow.nextSibling);
        } else {
            tbody.insertBefore(draggedRow, targetRow);
        }
    }
}

function onDrop(event) {
    event.preventDefault();
    if (draggedRow) {
        draggedRow.style.opacity = "1";
        draggedRow = null;
    }
}

function removeRow(button) {
    button.closest('tr').remove();
}

function addRow(tableId) {
    const table = document.getElementById(tableId);
    const tbody = table.querySelector('tbody');
    const headers = table.querySelectorAll('thead th');
    const columnCount = headers.length;

    const newRow = tbody.insertRow();
    newRow.setAttribute("draggable", "true");
    newRow.setAttribute("ondragstart", "onDragStart(event)");
    newRow.setAttribute("ondragover", "onDragOver(event)");
    newRow.setAttribute("ondrop", "onDrop(event)");

    for (let i = 0; i < columnCount; i++) {
        const cell = newRow.insertCell();
        if (i === columnCount - 1) {
            cell.innerHTML = `<button type="button" class="btn btn-sm btn-danger" onclick="removeRow(this)">Remove</button>`;
        } else {
            cell.innerHTML = `<input type="text" placeholder="Enter value" required>`;
        }
    }
}
