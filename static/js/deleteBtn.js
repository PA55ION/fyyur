const deleteBtn = document.querySelectorAll(".delete-btn");
for(let i = 0; i < deleteBtn.length; i++) {
    const btn = deleteBtn[i]
    btn.onclick = function(e) {
        const venueId = e.target.dataset["id"];
        console.log("Button was clicked", venueId);
        fetch(`venues/${venueId}`, {
            method: 'DELETE'
        })
    }
}



