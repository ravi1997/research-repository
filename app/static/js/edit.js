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

function addAuthor() {
    const table = document.getElementById('authors-table');
    const tbody = table.querySelector('tbody');
    const index = tbody.rows.length + 1; // Dynamically determine the row index
    const newRow = tbody.insertRow();

    // Set attributes for dragging functionality
    newRow.setAttribute("draggable", "true");
    newRow.setAttribute("ondragstart", "onDragStart(event)");
    newRow.setAttribute("ondragover", "onDragOver(event)");
    newRow.setAttribute("ondrop", "onDrop(event)");

    // Create cells
    const cell1 = newRow.insertCell();
    const cell2 = newRow.insertCell();
    const cell3 = newRow.insertCell();
    const cell4 = newRow.insertCell();
    const cell5 = newRow.insertCell();

    // Set cell content
    cell1.style.display = "none";
    cell1.innerHTML = `<input type="text" name="authors[${index}][id]" value="None-Type">`; // Use template literals
    cell2.innerHTML = `<input type="text" name="authors[${index}][fullName]" value="" required>`;
    cell3.innerHTML = `<input type="text" name="authors[${index}][affiliation]" value="">`;
    cell4.innerHTML = `<input type="text" name="authors[${index}][abbreviation]" value="">`;
    cell5.innerHTML = `<button type="button" class="btn btn-sm btn-danger" onclick="removeRow(this)">Remove</button>`;
}

function addKeyword() {
    const table = document.getElementById('keywords-table');
    const tbody = table.querySelector('tbody');
    const index = tbody.rows.length + 1; // Dynamically determine the row index
    const newRow = tbody.insertRow();

    // Set attributes for dragging functionality
    newRow.setAttribute("draggable", "true");
    newRow.setAttribute("ondragstart", "onDragStart(event)");
    newRow.setAttribute("ondragover", "onDragOver(event)");
    newRow.setAttribute("ondrop", "onDrop(event)");

    // Create cells
    const cell1 = newRow.insertCell();
    const cell2 = newRow.insertCell();
    const cell3 = newRow.insertCell();

    // Set cell content
    cell1.style.display = "none";
    cell1.innerHTML = `<input type="text" name="keywords[${index}][id]" value="None-Type">`; // Use template literals
    cell2.innerHTML = `<input type="text" name="keywords[${index}][keyword]" value="" required>`;
    cell3.innerHTML = `<button type="button" class="btn btn-sm btn-danger" onclick="removeRow(this)">Remove</button>`;
}


function addLink() {
    const table = document.getElementById('links-table');
    const tbody = table.querySelector('tbody');
    const index = tbody.rows.length + 1; // Dynamically determine the row index
    const newRow = tbody.insertRow();

    // Set attributes for dragging functionality
    newRow.setAttribute("draggable", "true");
    newRow.setAttribute("ondragstart", "onDragStart(event)");
    newRow.setAttribute("ondragover", "onDragOver(event)");
    newRow.setAttribute("ondrop", "onDrop(event)");

    // Create cells
    const cell1 = newRow.insertCell();
    const cell2 = newRow.insertCell();
    const cell3 = newRow.insertCell();

    // Set cell content
    cell1.style.display = "none";
    cell1.innerHTML = `<input type="text" name="links[${index}][id]" value="None-Type">`; // Use template literals
    cell2.innerHTML = `<input type="text" name="links[${index}][link]" value="" required>`;
    cell3.innerHTML = `<button type="button" class="btn btn-sm btn-danger" onclick="removeRow(this)">Remove</button>`;
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
        } else if (i === 0) {
            cell.style.display = "none"; // Hide the first column
            cell.innerHTML = `<input type="text" placeholder="Enter value">`;
        } else if (i === 1) {
            cell.innerHTML = `<input type="text" placeholder="Enter value" required>`;
        } else {
            cell.innerHTML = `<input type="text" placeholder="Enter value">`;
        }
    }
}


async function submitForm(event) {
    event.preventDefault();  // Prevent the default form submission

    const salt = getCookie("Session-SALT");  // Assuming the salt cookie is named "salt"
    if (!salt) {
        console.error("Salt not found in cookies.");
        return;
    }
    const form = document.getElementById("edit-form");
    const formData = new FormData(form);
    const formDataJson = Object.fromEntries(formData.entries())
    const authorTable = document.querySelector("#authors-table");

    // Get the current order of rows in the table
    const authorRows = Array.from(authorTable.querySelectorAll("tr")); // Select all rows in the table
    const authors = []; // Initialize an array to store authors

    authorRows.forEach((row, index) => {
        const inputs = row.querySelectorAll("input"); // Get all inputs in the current row
        const author = { sequence_number: index }; // Assign sequence number based on current row order

        inputs.forEach(input => {
            const match = input.name.match(/^authors\[\d+\]\[(\w+)\]$/); // Match the field name (e.g., fullName, affiliation)
            if (match) {
                const field = match[1];
                author[field] = input.value; // Add the field and value to the author object
                delete formDataJson[input.name];
            }
        });

        // Only add the author if it has relevant fields
        if (Object.keys(author).length > 1) {
            authors.push(author);
        }
    });

    const keywordTable = document.querySelector("#keywords-table");

    // Get the current order of rows in the table
    const keywordRows = Array.from(keywordTable.querySelectorAll("tr")); // Select all rows in the table
    const keywords = []; // Initialize an array to store authors

    keywordRows.forEach((row, index) => {
        const inputs = row.querySelectorAll("input"); // Get all inputs in the current row
        const keyword = {  }; // Assign sequence number based on current row order

        inputs.forEach(input => {
            const match = input.name.match(/^keywords\[\d+\]\[(\w+)\]$/); // Match the field name (e.g., fullName, affiliation)
            if (match) {
                const field = match[1];
                keyword[field] = input.value; // Add the field and value to the author object
                delete formDataJson[input.name];
            }
        });

        // Only add the author if it has relevant fields
        if (Object.keys(keyword).length > 1) {
            keywords.push(keyword);
        }
    });


    

    const linkTable = document.querySelector("#links-table");

    // Get the current order of rows in the table
    const linkRows = Array.from(linkTable.querySelectorAll("tr")); // Select all rows in the table
    const links = []; // Initialize an array to store authors

    linkRows.forEach((row, index) => {
        const inputs = row.querySelectorAll("input"); // Get all inputs in the current row
        const link = {}; // Assign sequence number based on current row order

        inputs.forEach(input => {
            const match = input.name.match(/^links\[\d+\]\[(\w+)\]$/); // Match the field name (e.g., fullName, affiliation)
            if (match) {
                const field = match[1];
                link[field] = input.value; // Add the field and value to the author object
                delete formDataJson[input.name];
            }
        });

        // Only add the author if it has relevant fields
        if (Object.keys(link).length > 1) {
            links.push(link);
        }
    });



    formDataJson['links'] = links;

    formDataJson['keywords'] = keywords;
    formDataJson['authors'] = authors;
    formDataJson['uuid'] = article_uuid;


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
            console.log("Succesfull");
        } else {
            // Handle errors, if any (e.g., show an error message)
            console.error("Form submission failed.");
        }
    } catch (error) {
        console.error("An error occurred:", error);
    }
}

async function logout() {
    try {
        const response = await fetch("../researchrepository/api/auth/logout", {
            method: "GET",
        });

        if (response.ok) {
            window.location.href = "../researchrepository/login";
        } else {
            const error = await response.json()["message"];
            showAlert(error, false);
        }
    } catch (error) {
        console.error(error);
        showAlert(error, false);
    }
}

