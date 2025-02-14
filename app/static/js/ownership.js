// Function to display the modal
function showModal(title, message) {
    // Set modal content
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-message').textContent = message;

    // Show the modal
    document.getElementById('status-modal').classList.remove('hidden');
}

// Function to close the modal
document.getElementById('close-modal').addEventListener('click', function () {
    document.getElementById('status-modal').classList.add('hidden');
});


// Function to handle the author click (success or failure)
function handleAuthorClick(authorId) {
    // Perform the operation (example: making a fetch request to the server)
    fetch(`/api/article/ownership/${authorId}`)
        .then(response => {
            if (response.ok) {
                // Show success message
                showModal('Success', 'The author has been successfully updated.');
                // Reload the page on success
                setTimeout(() => {
                    const authorElement = document.querySelector(`[data-author-uuid="${authorId}"]`);

                    // To apply some effect or access the element
                    if (authorElement) {
                        // Do something with the author element, e.g., change the background color
                        authorElement.classList.toggle('font-bold');
                    } 
                }, 2000);
            } else {
                // Show failure message
                showModal('Failure', 'There was an error processing your request. Please try again.');
            }
        })
        .catch(error => {
            // Show failure message if the fetch fails
            showModal('Failure', 'There was an error processing your request. Please try again.');
        });
}





const uuidApiBaseUrl = "/api/search/search"; // CHANGE THIS TO YOUR ACTUAL API
const articleDetailsApiUrl = "/api/article"; // CHANGE THIS TO YOUR ACTUAL API

let articleUUIDs = [];
let all_authors = [];
// let all_keywords = [];
let all_journals = [];


function navigateToPage(pageNumber) {
    let totalPages = document.getElementById('total_pages').value;
    let entry = document.getElementById('limit').value;
    if (pageNumber < 1 || pageNumber > totalPages) return;
    currentPage = pageNumber;

    // Regenerate paginations for both top and bottom

    console.log(`Navigated to page: ${currentPage}`);
    document.getElementById('offset').value = (currentPage - 1) * entry
    loadArticles();
}

function jumpToPage(value) {
    let pageNumber = parseInt(value, 10);
    if (!isNaN(pageNumber)) {
        navigateToPage(pageNumber);
    }
}

function createPagination(containerId, currentPage, totalPages) {
    let paginationContainer = document.getElementById(containerId);
    paginationContainer.innerHTML = ""; // Clear existing pagination

    let paginationDiv = document.createElement("div");
    paginationDiv.classList.add("pagination", "flex", "flex-row", "align-middle", "items-center", "gap-2", "m-4");

    function createButton(label, targetPage, isDisabled) {
        let button = document.createElement("button");
        button.type = "button";
        button.innerText = label;
        button.className = isDisabled
            ? "bg-blue-400 text-white font-bold py-2 px-2 text-sm xl:px-4 xl:text-md rounded cursor-not-allowed"
            : "bg-blue-800 hover:bg-blue-900 text-white font-bold py-2 px-2 text-sm xl:px-4 xl:text-md border border-blue-700 rounded";
        button.disabled = isDisabled;
        if (!isDisabled) {
            button.onclick = () => navigateToPage(targetPage);
        }
        return button;
    }

    // First Button
    paginationDiv.appendChild(createButton("First", 1, currentPage <= 1));

    // Previous Button
    paginationDiv.appendChild(createButton("Previous", currentPage - 1, currentPage <= 1));

    // Page Info
    let pageInfoDiv = document.createElement("div");
    pageInfoDiv.classList.add("flex", "items-center", "justify-center");
    pageInfoDiv.innerHTML = `Page &nbsp;
        <input id="${containerId}-page-number" aria-label="GoToPageNumber" type="text" min="1" value="${currentPage}" 
            class="w-16 p-2 border rounded text-center  text-black
                 dark:border-gray-700 dark:bg-gray-200 dark:text-black focus:outline-none focus:ring-2 focus:ring-blue-500"
            onblur="jumpToPage(this.value)" /> &nbsp; of &nbsp;<span>${totalPages}</span>`;
    paginationDiv.appendChild(pageInfoDiv);

    // Next Button
    paginationDiv.appendChild(createButton("Next", currentPage + 1, currentPage >= totalPages));

    // Last Button
    paginationDiv.appendChild(createButton("Last", totalPages, currentPage >= totalPages));

    paginationContainer.appendChild(paginationDiv);
}

console.log(document.getElementById('searchBox'));

document.getElementById('searchBox').addEventListener('keypress', function (e) {
    document.getElementById('offset').value = 0
    document.getElementById('query').value = document.getElementById('searchBox').value
    if (e.key === 'Enter') {
        document.getElementById('filter-form').submit();
    }
});

function constructUuidApiUrl() {
    let params = new URLSearchParams();

    // Retrieve form values
    let offset = document.getElementById("offset").value;
    let limit = document.getElementById("limit").value;
    let query = document.getElementById("query").value;
    let startDate = document.getElementById("start-date").value;
    let endDate = document.getElementById("end-date").value;
    let authors = filters.authors || [];
    // let keywords = filters.keywords || [];
    let journals = filters.journals || [];
    // console.log(authors);
    // Append parameters if they exist
    if (offset) params.append("offset", offset);
    if (limit) params.append("limit", limit);
    if (query) params.append("query", query);
    if (startDate) params.append("start_date", startDate);
    if (endDate) params.append("end_date", endDate);
    if (authors.length > 0) params.append("authors", authors.join(","));
    // if (keywords.length > 0) params.append("keywords", keywords.join(","));
    if (journals.length > 0) params.append("journals", journals.join(' | '));

    return `${uuidApiBaseUrl}?${params.toString()}`;
}

// Function to get checked values from checkbox lists
function getCheckedValues(containerId) {
    let selectedValues = [];
    let checkboxes = document.querySelectorAll(`#${containerId} input[type="checkbox"]:checked`);
    checkboxes.forEach((checkbox) => {
        selectedValues.push(checkbox.value);
    });
    return selectedValues;
}

async function fetchArticleDetails(uuid) {
    try {
        let response = await fetch(`${articleDetailsApiUrl}/${uuid}`);
        if (!response.ok) {
            throw new Error(`Error fetching article ${uuid}`);
        }
        return await response.json();
    } catch (error) {
        console.error(error);
        return null;
    }
}

// Function to fetch article UUIDs
async function fetchArticleUUIDs() {
    let uuidApiUrl = constructUuidApiUrl(); // Construct API URL with form values

    try {
        let response = await fetch(uuidApiUrl);
        if (!response.ok) {
            throw new Error("Error fetching article UUIDs");
        }
        return await response.json(); // Assuming the API returns a list of UUIDs
    } catch (error) {
        console.error(error);
        return [];
    }
}


function renderArticle(article) {
    if (!article) return;

    let list = document.getElementById("results");

    let ul = document.createElement("ul");
    let li = document.createElement("li");
    li.id = article.uuid + "-uuid";
    li.classList.add("w-full");

    let divContainer = document.createElement("div");
    divContainer.classList.add("flex", "w-full", "flex-row", "ps-3");

    let label = document.createElement("label");
    label.setAttribute("for", article.uuid);
    label.classList.add("w-full");

    let divContent = document.createElement("div");
    divContent.id = article.uuid;
    divContent.classList.add(
        "mx-auto", "my-2", "flex", "flex-row", "justify-between",
        "overflow-hidden", "rounded", "border", "p-2", "shadow-lg",
        "duration-100",
        "dark:border-gray-300"
    );

    let divText = document.createElement("div");

    let titleSpan = document.createElement("span");
    titleSpan.classList.add("font-bold");
    titleSpan.innerHTML = article.title;
    divText.appendChild(titleSpan);
    divText.appendChild(document.createElement("br"));

    // Authors
    article.authors.forEach((author, index) => {
        let authorElement;

        if (roles.includes("FACULTY")) {
            // Create an anchor tag for FACULTY role
            let authorLink = document.createElement("a");
            authorLink.href = "#";
            authorLink.classList.add("author-link");
            authorLink.setAttribute("data-author-id", author.employee_id);
            authorLink.setAttribute("data-author-uuid", author.id);

            authorLink.addEventListener("click", function (event) {
                event.preventDefault(); // Prevent any default action
                const authorId = this.getAttribute("data-author-uuid");
                handleAuthorClick(authorId);
            });


            // Create a span inside the anchor
            authorElement = document.createElement("span");
            authorElement.textContent = author.fullName;
            authorElement.classList.add("px-2", "hover:text-teal-100", "hover:bg-teal-900", "ease-in", "duration-100");

            // Apply bold styling if the author has an employee_id
            if (author.employee_id) {
                authorLink.classList.add("font-bold");
            }

            // Append the span to the anchor
            authorLink.appendChild(authorElement);
            divText.appendChild(authorLink);
        } else {
            // Create a standalone span for non-FACULTY roles
            authorElement = document.createElement("span");
            authorElement.textContent = author.fullName;
            authorElement.classList.add("px-2", "hover:text-teal-100", "hover:bg-teal-900", "ease-in", "duration-100");

            if (author.employee_id) {
                authorLink.classList.add("font-bold");
            }

            divText.appendChild(authorElement);
        }
    });


    divText.appendChild(document.createElement("br"));

    // Journal
    let journalSpan = document.createElement("span");
    journalSpan.classList.add("italic");
    journalSpan.innerHTML = article.journal || "";
    divText.appendChild(journalSpan);
    divText.appendChild(document.createElement("br"));

    // Publication Details
    divText.appendChild(document.createTextNode(`${article.publication_date || ''}. ${article.journal_volume || ''}`));
    if (article.journal_issue) {
        divText.appendChild(document.createTextNode(` (${article.journal_issue})`));
    }
    if (article.pages) {
        divText.appendChild(document.createTextNode(` :${article.pages}`));
    }
    divText.appendChild(document.createElement("br"));

    // PubMed ID
    if (article.pubmed_id) {
        let pubmedLink = document.createElement("a");
        pubmedLink.href = `https://pubmed.ncbi.nlm.nih.gov/${article.pubmed_id}`;
        pubmedLink.innerText = article.pubmed_id;
        divText.appendChild(pubmedLink);
        divText.appendChild(document.createElement("br"));
    }

    // DOI
    if (article.doi) {
        let doiText = document.createTextNode("DOI: ");
        let doiLink = document.createElement("a");
        doiLink.href = `https://doi.org/${article.doi}`;
        doiLink.target = "_blank";
        doiLink.innerText = article.doi;
        divText.appendChild(doiText);
        divText.appendChild(doiLink);
        divText.appendChild(document.createElement("br"));
    }

    // PubMed Central
    if (article.pmc_id) {
        let pmcText = document.createTextNode("PUBMED CENTRAL: ");
        let pmcLink = document.createElement("a");
        pmcLink.href = `https://www.ncbi.nlm.nih.gov/pmc/${article.pmc_id}`;
        pmcLink.target = "_blank";
        pmcLink.innerText = article.pmc_id;
        divText.appendChild(pmcText);
        divText.appendChild(pmcLink);
        divText.appendChild(document.createElement("br"));
    }

    // Created At
    if (article.created_at) {
        divText.appendChild(document.createTextNode(`Created at: ${article.created_at}`));
        divText.appendChild(document.createElement("br"));
    }

    divContent.appendChild(divText);

    // View Icon
    let divIcon = document.createElement("div");
    divIcon.classList.add("flex", "flex-col", "gap-2", "p-2", "align-middle");

    let viewLink = document.createElement("a");
    viewLink.href = `/article/${article.uuid}`;
    viewLink.target = "_blank";
    viewLink.ariaLabel = "View Article : " + article.title;
    viewLink.innerHTML = `
                                <svg
                        width="24px"
                        height="24px"
                        viewBox="0 0 1024 1024"
                        class="icon"
                        version="1.1"
                        xmlns="http://www.w3.org/2000/svg"
                        >
                        <path
                            d="M94.433 536.378c49.818-67.226 110.761-124.854 180.172-166.808 35.333-21.356 62.64-33.686 99.016-45.698 17.076-5.638 34.511-10.135 52.088-13.898 23.033-4.932 28.596-5.483 49.577-7.228 76.233-6.333 138.449 4.648 210.869 33.643 3.581 1.435 10.361 4.513 18.987 8.594 8.488 4.013 16.816 8.358 25.086 12.801 18.349 9.861 36.004 20.974 53.173 32.756 31.245 21.442 62.37 49.184 91.227 79.147 20.218 20.991 39.395 43.706 56.427 66.689 14.436 19.479 38.301 29.282 60.985 15.991 19.248-11.276 30.491-41.417 15.991-60.984-101.194-136.555-243.302-247.3-415.205-272.778-165.834-24.575-325.153 31.855-452.148 138.262-46.849 39.252-86.915 85.525-123.221 134.518-14.5 19.567-3.258 49.708 15.991 60.984 22.685 13.291 46.549 3.488 60.985-15.991z"
                            fill="currentColor"
                        />
                        <path
                            d="M931.055 491.378c-49.817 67.228-110.761 124.856-180.173 166.811-35.332 21.354-62.639 33.684-99.015 45.694-17.076 5.641-34.512 10.137-52.09 13.902-23.032 4.931-28.593 5.48-49.576 7.225-76.233 6.336-138.449-4.648-210.869-33.642-3.582-1.436-10.362-4.514-18.987-8.595-8.488-4.015-16.816-8.357-25.087-12.801-18.348-9.862-36.003-20.974-53.172-32.755-31.245-21.443-62.37-49.184-91.227-79.149-20.218-20.99-39.395-43.705-56.427-66.69-14.436-19.479-38.3-29.279-60.985-15.991-19.249 11.276-30.491 41.419-15.991 60.984C118.65 672.929 260.76 783.677 432.661 809.15c165.834 24.578 325.152-31.854 452.148-138.259 46.85-39.256 86.915-85.528 123.222-134.521 14.5-19.564 3.257-49.708-15.991-60.984-22.685-13.287-46.55-3.487-60.985 15.992z"
                            fill="#C45FA0"
                        />
                        <path
                            d="M594.746 519.234c0.03 46.266-34.587 83.401-80.113 85.188-46.243 1.814-83.453-35.93-85.188-80.11-0.953-24.271-19.555-44.574-44.574-44.574-23.577 0-45.527 20.281-44.573 44.574 3.705 94.378 79.154 169.32 174.334 169.258 94.457-0.063 169.321-81.897 169.261-174.335-0.039-57.486-89.184-57.49-89.147-0.001z"
                            fill="#F39A2B"
                        />
                        <path
                            d="M430.688 514.818c0.876-45.416 37.262-81.797 82.677-82.672 45.438-0.875 81.824 38.571 82.673 82.672 1.105 57.413 90.256 57.521 89.147 0-1.827-94.791-77.028-169.994-171.82-171.82-94.787-1.827-170.049 79.785-171.824 171.82-1.108 57.522 88.04 57.413 89.147 0z"
                            fill="#E5594F"
                        />
                        </svg>`;
    divIcon.appendChild(viewLink);

    divContent.appendChild(divIcon);
    label.appendChild(divContent);
    divContainer.appendChild(label);
    li.appendChild(divContainer);
    ul.appendChild(li);
    list.appendChild(ul);
}

function updateResults(currentPage, entriesPerPage, totalArticles) {
    let string1 = (currentPage - 1) * entriesPerPage + 1;
    let string2 = string1 + totalArticles - 1;

    document.getElementById("showResults").textContent =
        `Showing records from ${string1} to ${string2}`;
}


function showActiveFilters(container_id, arr) {
    let container = document.getElementById(container_id);
    container.innerHTML = '';
    arr.forEach((author, index) => {
        let divelement = document.createElement('div');
        divelement.classList.add("flex", "items-center", "bg-blue-200", "px-3", "py-1", "rounded-full", "inline-block", "mr-2",
            "mb-2");

        let textSpan = document.createElement("span");
        textSpan.textContent = author;
        textSpan.classList.add("mr-2", "text-black");

        let removeBtn = document.createElement("button");
        removeBtn.innerHTML = "&times;"; // Cross symbol (×)
        removeBtn.classList.add("text-red-600", "font-bold", "hover:text-red-800", "cursor-pointer");
        removeBtn.onclick = function () {
            removeFilter(author, container_id);

        };

        divelement.appendChild(textSpan);
        divelement.appendChild(removeBtn);
        container.appendChild(divelement);
    });
}


function removeFilter(author, container_id) {

    if (container_id.includes('author')) {
        filters.authors = filters.authors.filter(item => item !== author); // Remove selected author
        fetchAuthors();
        showActiveFilters(container_id, filters.authors); // Re-render the updated list
    }
    // else if (container_id.includes('keyword')) {
    //     filters.keywords = filters.keywords.filter(item => item !== author); // Remove selected author
    //     fetchKeywords();
    //      showActiveFilters(container_id, filters.keywords); // Re-render the updated list
    // }
    else if (container_id.includes('journal')) {
        filters.journals = filters.journals.filter(item => item !== author); // Remove selected author
        fetchJournals();
        showActiveFilters(container_id, filters.journals); // Re-render the updated list
    }
}

// Fetch and load all articles
async function loadArticles() {
    let articleUUIDs = await fetchArticleUUIDs();
    let params = new URLSearchParams();

    // Retrieve form values
    let offset = document.getElementById("offset").value;
    let limit = document.getElementById("limit").value;

    let list = document.getElementById("results");
    list.innerHTML = '';
    let currentPage = Math.floor(offset / limit) + 1;
    let totalArticles_page = articleUUIDs.articles.length;
    let totalArticles = articleUUIDs.total_articles;
    let totalPages = Math.floor(totalArticles / limit) + 1;

    document.getElementById('total_pages').value = totalArticles;
    // console.log(currentPage);
    // console.log(totalPages);
    // console.log(limit);
    // console.log(totalArticles);

    createPagination("pagination-top", currentPage, totalPages);
    createPagination("pagination-bottom", currentPage, totalPages);
    updateResults(currentPage, limit, totalArticles_page);


    showActiveFilters('active-author-filters', filters.authors || []);
    showActiveFilters('active-journal-filters', filters.journals || []);
    // showActiveFilters('active-keyword-filters', filters.keywords || []);


    for (let uuid of articleUUIDs.articles) {
        let article = await fetchArticleDetails(uuid);
        if (article) renderArticle(article);
    }

}

let debounceTimer;

function debounceFilterAuthors() {
    clearTimeout(debounceTimer); // Clear any existing timer
    debounceTimer = setTimeout(() => {
        filterAuthors(); // Call filter function after delay
    }, 500); // 300ms delay (adjustable)
}


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

// Function to manage authors filter array
function manageAuthorFilter(authorName) {
    if (!filters.hasOwnProperty("authors")) {
        filters["authors"] = [];
    }

    if (!filters.authors.includes(authorName)) {
        filters.authors.push(authorName); // Add author if not already in the list
    }
    showActiveFilters('active-author-filters', filters.authors);
}


// Function to filter keywords based on search input
// function filterKeywords() {
//     const searchInput = document.getElementById("keyword-search").value.toLowerCase();
//     const allKeywordItems = document.querySelectorAll("#keyword-options .keyword-item");

//     allKeywordItems.forEach(item => {
//         const label = item.querySelector("label").textContent.toLowerCase();
//         if (label.includes(searchInput)) {
//             item.style.display = ""; // Show the keyword if it matches
//         } else {
//             item.style.display = "none"; // Hide the keyword if it doesn't match
//         }
//     });
// }

// Function to reorder keywords: Move checked items to the top
// function reorderKeywords(keywordName) {
//     if (!filters.hasOwnProperty("keywords")) {
//         filters["keywords"] = [];
//     }

//     if (!filters.keywords.includes(keywordName)) {
//         filters.keywords.push(keywordName); // Add author if not already in the list
//     }

//     showActiveFilters('active-keyword-filters', filters.keywords);
// }

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
function reorderJournals(journalName) {
    if (!filters.hasOwnProperty("journals")) {
        filters["journals"] = [];
    }

    if (!filters.journals.includes(journalName)) {
        filters.journals.push(journalName); // Add author if not already in the list
    }

    showActiveFilters('active-journal-filters', filters.journals);
}


document.addEventListener("DOMContentLoaded", function () {
    loadArticles();
    fetchAuthors();
    // fetchKeywords();
    fetchJournals();
});

async function fetchAuthors() {
    await fetchData("/api/search/authors", "author-options", "author", "authors", manageAuthorFilter, filters.authors || [], 500);
}

// async function fetchKeywords() {
//     await fetchData("/api/search/keywords", "keyword-options", "keyword", "keywords", reorderKeywords, filters.keywords || [],50);
// }

async function fetchJournals() {
    await fetchData("/api/search/journals", "journal-options", "journal", "journals", reorderJournals, filters.journals || [], 50);
}


async function fetchData(url, containerId, itemname, nameAttr, changeHandler, selectedItems, max) {
    try {
        let query = document.getElementById('query').value;

        let response = await fetch(url + '?query=' + query);
        let items = await response.json();

        let container = document.getElementById(containerId);
        container.innerHTML = ""; // Clear existing content

        if (itemname == "author") {
            all_authors = items;
        }
        // else if (itemname == "keyword") {
        //     all_keywords = items;
        // }
        else if (itemname == "journal") {
            all_journals = items;
        }

        items.slice(0, Math.min(max, items.length)).forEach((item, index) => {
            let itemDiv = document.createElement("div");
            itemDiv.classList.add(`${itemname}-item`, "flex", "flex-row", "justify-between", "items-center");

            let checkbox = document.createElement("input");
            checkbox.type = "checkbox";
            checkbox.id = `${nameAttr}-${index}`;
            checkbox.name = nameAttr;
            checkbox.value = item.name;



            // ✅ Set onchange as function reference, not a string
            checkbox.onchange = function () {
                if (this.checked) {
                    changeHandler(item.name);
                } else {
                    removeFilter(item.name, `active-${itemname}-filters`);
                }
            };



            // ✅ Check if the item is already selected
            if (selectedItems.includes(item.name)) {
                checkbox.checked = true;
            }
            let itemDiv1 = document.createElement("div");
            let label = document.createElement("label");
            label.htmlFor = `${nameAttr}-${index}`;
            label.textContent = item.name;
            label.classList.add("p-2");

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
