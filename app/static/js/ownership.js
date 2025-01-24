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

// Attach the handleAuthorClick function to the author links
document.querySelectorAll('.author-link').forEach(function (authorLink) {
    authorLink.addEventListener('click', function (event) {
        event.preventDefault(); // Prevent the default behavior of the link

        // Get the author ID from the 'data-author-id' attribute
        const authorId = this.getAttribute('data-author-id');
        handleAuthorClick(authorId); // Call the function to handle the click
    });
});
