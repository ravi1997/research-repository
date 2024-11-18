function navigateToPage(page, entry,total_pages) {
    // Check if the page is valid
    if (page > 0 && page <= total_pages) {
        // Redirect to the new page
        window.location.href = `/researchrepository/repository?page=${page}&entry=${entry}`;
    }
}
