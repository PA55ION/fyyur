const deleteBtn = document.querySelectorAll(".delete-btn");
for(let i = 0; i < deleteBtn.length; i++) {
    const btn = deleteBtn[i]
    btn.onclick = function(e) {
        const venueId = e.target.dataset["id"];
        e.target.parentElement.removeChild(e.target);
        console.log("Button was clicked", venueId);
        fetch(`/venues/${venueId}`, {
            method: 'DELETE',
        })
        .then(function() {
            window.location.href = '/venues';
        })
        .catch(function(e) {
            console.log('error', e)
        })
    }
}



