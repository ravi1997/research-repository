
function tostifyCustomClose(el) {
    const parent = el.closest('.toastify');
    const close = parent.querySelector('.toast-close');
    close.click();
}


async function deleteArticle(uuid) {

    const response = await fetch('../api/article/'+uuid, {
        method: "DELETE",
    });

    if (response.ok) {
        const toastMarkup = `
        <div class="flex p-4">
        <p class="text-sm text-gray-700 dark:text-neutral-400">Item Deleted successfully.</p>
        <div class="ms-auto">
          <button onclick="tostifyCustomClose(this)" type="button" class="inline-flex shrink-0 justify-center items-center size-5 rounded-lg text-gray-800 opacity-50 hover:opacity-100 focus:outline-none focus:opacity-100 dark:text-white" aria-label="Close">
            <span class="sr-only">Close</span>
            <svg class="shrink-0 size-4" xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 6 6 18"></path><path d="m6 6 12 12"></path></svg>
          </button>
        </div>
      </div>
    `;
        document.getElementById(uuid+"-uuid").classList.add("hidden");
        document.getElementById("count").innerHTML = parseInt(document.getElementById("count").innerHTML, 10) - 1 ;
        showCloseButton()
        Toastify({
            text: toastMarkup,
            className: "hs-toastify-on:opacity-100 opacity-0 fixed -top-[150px] right-[20px] z-[90] transition-all duration-300 w-[320px] bg-white text-sm text-gray-700 border border-gray-200 rounded-xl shadow-lg [&>.toast-close]:hidden dark:bg-neutral-800 dark:border-neutral-700 dark:text-neutral-400",
            duration: 1000,
            close: true,
            escapeMarkup: false
        }).showToast();

    } else {
        const error = await response.json();
        document.getElementById("message").innerText = "Error: " + error.error;
    }
}

async function resolveDuplicate(uuid) {

    const response = await fetch('../api/article/duplicate/' + uuid + '/resolved', {
        method: "DELETE",
    });

    if (response.ok) {
        var checkedBoxes = document.querySelectorAll('input[name=articleCheckBox]');
        for (var i = 0; i < checkedBoxes.length; i++) {
            deleteArticle(checkedBoxes[i].id);
        }
    } else {
        const error = await response.json();
        document.getElementById("message").innerText = "Error: " + error.error;
    }
}


function showCloseButton(){
    if (parseInt(document.getElementById("count").innerHTML, 10) == 0){
        document.getElementById('mainbody').classList.add("hidden");
        document.getElementById('closebody').classList.remove("hidden");
    }
}



function articleCheck(){
    var checkedBoxes = document.querySelectorAll('input[name=articleCheckBox]:checked');
    if (checkedBoxes.length > 0) {
        document.getElementById('deleteButton').classList.remove("hidden");
    } else {
        document.getElementById('deleteButton').classList.add("hidden");
    }
}

async function deleteCheckArticles() {
    var checkedBoxes = document.querySelectorAll('input[name=articleCheckBox]:checked');
    for(var i=0;i<checkedBoxes.length;i++){
        deleteArticle(checkedBoxes[i].id);
    }
    articleCheck()
}



