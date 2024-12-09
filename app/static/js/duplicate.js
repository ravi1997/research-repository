async function deleteArticle(uuid) {

    const response = await fetch('../api/article/'+uuid, {
        method: "DELETE",
    });

    if (response.ok) {
        document.getElementById(uuid).classList.add("hidden");
    } else {
        const error = await response.json();
        document.getElementById("message").innerText = "Error: " + error.error;
    }

    
}