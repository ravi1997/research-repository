function navigateToPage(page, entry,total_pages) {
    // Check if the page is valid
    if (page > 0 && page <= total_pages) {
        // Redirect to the new page
        window.location.href = `/researchrepository/repository?page=${page}&entry=${entry}`;
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