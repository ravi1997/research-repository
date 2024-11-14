
let currentPage = 1;
let totalPages = 1;

function fetchTableData(page) {
    fetch(`/researchrepository/api/article/table?page=${page}`)
        .then(response => response.json())
        .then(data => {
            currentPage = data.page;
            totalPages = data.total_pages;
            renderTable(data.data);
            updatePageInfo();
        });
}

function renderTable(data) {
    const tableBody = document.getElementById('table-body');
    tableBody.innerHTML = '';
    data.forEach(item => {
        const row = document.createElement('tr');
        row.innerHTML = `
    <td>${item.title}</td>
    <td>${item.authors.map(author => author.fullName).join('; ')}</td>
    <td>${item.publication_date || ''}</td>
    <td>${item.journal || ''}</td>
    <td>${item.journal_issue || ''}</td>
    <td>${item.journal_volume || ''}</td>
    <td>${item.pages || ''}</td>
    <td>${item.keywords.map(keyword => keyword.keyword).join('; ')}</td>
    <td>${item.pubmed_id || ''}</td>
    <td>${item.doi ? `<a href="https://doi.org/${item.doi}" target="_blank">${item.doi}</a>` : ''}</td>
    <td><a href="/researchrepository/article/${item.uuid}">View</a></td>
    `;
        tableBody.appendChild(row);
    });
}

function updatePageInfo() {
    document.getElementById('page-info').innerText = `Page ${currentPage} of ${totalPages}`;
}

function prevPage() {
    if (currentPage > 1) {
        fetchTableData(currentPage - 1);
    }
}

function nextPage() {
    if (currentPage < totalPages) {
        fetchTableData(currentPage + 1);
    }
}

// Fetch initial data
fetchTableData(currentPage);