function navigateToPage(page, entry, total_pages) {
    // Check if the page is valid
    if (page > 0 && page <= total_pages) {
        document.getElementById('offset').value = (page-1) * entry
        document.getElementById('filter-form').submit();
    }
}

function jumpToPage(pageNumber, entry, totalPages) {
    const page = parseInt(pageNumber, 10);
    if (!isNaN(page) && page >= 1 && page <= totalPages) {
        navigateToPage(page, entry, totalPages);
    } else {
        alert(`Please enter a valid page number between 1 and ${totalPages}`);
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
}


document.addEventListener("DOMContentLoaded", function () {
    fetchAuthors();
    fetchKeywords();
    fetchJournals();

});

async function fetchAuthors() {
    await fetchData("/api/search/authors", "author-options", "author", "authors", reorderAuthors, filters.authors || []);
}

async function fetchKeywords() {
    await fetchData("/api/search/keywords", "keyword-options", "keyword", "keywords", reorderKeywords, filters.keywords || []);
}

async function fetchJournals() {
    await fetchData("/api/search/journals", "journal-options", "journal", "journals", reorderJournals, filters.journals || []);
}


async function fetchData(url, containerId, itemname, nameAttr, changeHandler, selectedItems) {
    try {
        let query = document.getElementById('query').value;

        let response = await fetch(url + '?query=' + query);
        let items = await response.json();

        let container = document.getElementById(containerId);
        container.innerHTML = ""; // Clear existing content

        items.forEach((item, index) => {
            let itemDiv = document.createElement("div");
            itemDiv.classList.add(`${itemname}-item`, "flex", "flex-row", "justify-between", "items-center");

            let checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.id = `${nameAttr}-${index}`;
            checkbox.name = nameAttr;
            checkbox.value = item.name;



            // ✅ Set onchange as function reference, not a string
            checkbox.onchange = changeHandler;

            // ✅ Check if the item is already selected
            if (selectedItems.includes(item.name)) {
                checkbox.checked = true;
            }
            let itemDiv1 = document.createElement("div");
            let label = document.createElement("label");
            label.htmlFor = `${nameAttr}-${index}`;
            label.textContent = item.name;
            label.classList.add("text-gray-700");

            let count = document.createElement("span");
            count.textContent = item.article_count;

            itemDiv1.appendChild(checkbox);
            itemDiv1.appendChild(label);
            itemDiv.appendChild(itemDiv1);
            itemDiv.appendChild(count);
            container.appendChild(itemDiv);
        });
    } catch (error) {
        console.error(`Error fetching ${nameAttr}:`, error);
    }
}
