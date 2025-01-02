function navigateToPage(page, entry, total_pages) {
    // Check if the page is valid
    if (page > 0 && page <= total_pages) {
        document.getElementById('offset').value = (page-1) * entry
        document.getElementById('filter-form').submit();
    }
}

document.getElementById('search').addEventListener('keypress', function (e) {
    document.getElementById('offset').value = 0
    document.getElementById('query').value = document.getElementById('search').value
    if (e.key === 'Enter') {
        document.getElementById('filter-form').submit();
    }
});

// Function to filter authors based on search input
function filterAuthors() {
    const searchInput = document.getElementById("author-search").value.toLowerCase();
    const allAuthorItems = document.querySelectorAll("#author-options .author-item");

    allAuthorItems.forEach(item => {
        const label = item.querySelector("label").textContent.toLowerCase();
        if (label.includes(searchInput)) {
            item.style.display = ""; // Show the author if it matches
        } else {
            item.style.display = "none"; // Hide the author if it doesn't match
        }
    });
}

// Function to reorder authors: Move checked items to the top
function reorderAuthors() {
    const authorOptionsDiv = document.getElementById("author-options");
    const allAuthorItems = Array.from(authorOptionsDiv.querySelectorAll(".author-item"));

    // Separate checked and unchecked items
    const checkedItems = [];
    const uncheckedItems = [];

    allAuthorItems.forEach(item => {
        const checkbox = item.querySelector("input[type='checkbox']");
        if (checkbox.checked) {
            checkedItems.push(item);
        } else {
            uncheckedItems.push(item);
        }
    });

    // Clear the list and reappend in the desired order
    authorOptionsDiv.innerHTML = "";
    checkedItems.forEach(item => authorOptionsDiv.appendChild(item));
    uncheckedItems.forEach(item => authorOptionsDiv.appendChild(item));
}

// Function to filter keywords based on search input
function filterKeywords() {
    const searchInput = document.getElementById("keyword-search").value.toLowerCase();
    const allKeywordItems = document.querySelectorAll("#keyword-options .keyword-item");

    allKeywordItems.forEach(item => {
        const label = item.querySelector("label").textContent.toLowerCase();
        if (label.includes(searchInput)) {
            item.style.display = ""; // Show the keyword if it matches
        } else {
            item.style.display = "none"; // Hide the keyword if it doesn't match
        }
    });
}

// Function to reorder keywords: Move checked items to the top
function reorderKeywords() {
    const keywordOptionsDiv = document.getElementById("keyword-options");
    const allKeywordItems = Array.from(keywordOptionsDiv.querySelectorAll(".keyword-item"));

    const checkedItems = [];
    const uncheckedItems = [];

    allKeywordItems.forEach(item => {
        const checkbox = item.querySelector("input[type='checkbox']");
        if (checkbox.checked) {
            checkedItems.push(item);
        } else {
            uncheckedItems.push(item);
        }
    });

    keywordOptionsDiv.innerHTML = "";
    checkedItems.forEach(item => keywordOptionsDiv.appendChild(item));
    uncheckedItems.forEach(item => keywordOptionsDiv.appendChild(item));
}

// Function to filter journals based on search input
function filterJournals() {
    const searchInput = document.getElementById("journal-search").value.toLowerCase();
    const allJournalItems = document.querySelectorAll("#journal-options .journal-item");

    allJournalItems.forEach(item => {
        const label = item.querySelector("label").textContent.toLowerCase();
        if (label.includes(searchInput)) {
            item.style.display = ""; // Show the journal if it matches
        } else {
            item.style.display = "none"; // Hide the journal if it doesn't match
        }
    });
}

// Function to reorder journals: Move checked items to the top
function reorderJournals() {
    const journalOptionsDiv = document.getElementById("journal-options");
    const allJournalItems = Array.from(journalOptionsDiv.querySelectorAll(".journal-item"));

    const checkedItems = [];
    const uncheckedItems = [];

    allJournalItems.forEach(item => {
        const checkbox = item.querySelector("input[type='checkbox']");
        if (checkbox.checked) {
            checkedItems.push(item);
        } else {
            uncheckedItems.push(item);
        }
    });

    journalOptionsDiv.innerHTML = "";
    checkedItems.forEach(item => journalOptionsDiv.appendChild(item));
    uncheckedItems.forEach(item => journalOptionsDiv.appendChild(item));
}

// Initialize lists to ensure checked items are at the top on page load
document.addEventListener("DOMContentLoaded", () => {
    reorderAuthors();
    reorderKeywords();
    reorderJournals();
});
