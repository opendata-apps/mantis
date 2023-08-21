let map;
let marker;
let cards = [];
let pages = [];
let currentPage = 0;

document.addEventListener('DOMContentLoaded', (event) => {
    loadData();
});

function loadData() {
    cards = Array.from(document.getElementsByClassName('report-card'));
    let pageSize = document.getElementById('pageSizeInput').value || 30; // default to 30 if no value selected

    pages = [];
    for (let i = 0; i < cards.length; i += pageSize) {
        pages.push(cards.slice(i, i + pageSize));
    }

    changePage(0);
}

function changePage(offset) {
    currentPage += offset;

    // make sure we don't go past the first or last page
    currentPage = Math.max(0, Math.min(pages.length - 1, currentPage));

    // disable/enable buttons
    document.getElementById('prevPageButton').disabled = (currentPage === 0);
    document.getElementById('nextPageButton').disabled = (currentPage === pages.length - 1);

    // update current page text
    document.getElementById('currentPage').textContent = 'Page ' + (currentPage + 1) + ' of ' + pages.length;

    // render the new page
    renderPage(currentPage);
}

function renderPage(pageNumber) {
    let container = document.getElementById('reportContainer');
    container.innerHTML = ''; // clear container

    pages[pageNumber].forEach((card) => {
        container.appendChild(card);
    });
}



document.addEventListener("DOMContentLoaded", function () {
    document.getElementById("sortInput").value = "id_asc";
    sortReports();
});

function sortReports() {
    let input = document.getElementById('sortInput').value;
    let cards = Array.from(document.getElementsByClassName('report-card'));

    cards.sort((a, b) => {
        let idA = a.getAttribute('data-report-id');
        let idB = b.getAttribute('data-report-id');
    
        switch (input) {
            case 'id_asc':
                return idA - idB;
            case 'id_desc':
                return idB - idA;
            default:
                return 0; // Default case to handle unexpected values
        }
    });

    let container = document.getElementById('reportContainer');

    cards.forEach((card) => {
        container.appendChild(card);
    });
}

function changeGender(id) {
    const selectElement = document.getElementById(`gender-${id}`);
    const newGender = selectElement.value;

    fetch(`/change_mantis_gender/${id}`, {
        method: 'POST',
        body: new URLSearchParams({ new_gender: newGender }),
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
            } else {
                console.error('Failed to change gender:', data.error);
            }
        });
}

function searchReports() {
    // Get input value
    let input = document.getElementById('searchInput').value.toLowerCase();
    let cards = document.getElementsByClassName('report-card');

    // Hide or show cards based on input
    for (let i = 0; i < cards.length; i++) {
        let id = cards[i].getAttribute('data-report-id');
        if (id.toLowerCase().includes(input)) {
            cards[i].style.display = "";
        } else {
            cards[i].style.display = "none";
        }
    }
}

document.addEventListener('DOMContentLoaded', function () {
    document.getElementById("sortInput").value = "id_asc";
    sortReports();

    // Add click event listeners for the modal backdrops
    document.getElementById('imageModalBackdrop').addEventListener('click', closeImageModal);
    //document.getElementById('modalBackdrop').addEventListener('click', closeModal);
});



// Function to toggle approve a sighting
function toggleApprove(id) {
    fetch('/toggle_approve_sighting/' + id, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Remove the approved card from the view
                removeCardFromView(id);
            } else {
                console.error('Failed to change approval status:', data.error);
            }
        })
        .catch(error => console.error('Error:', error));
}

function fetchReport(id) {
    fetch('/get_sighting/' + id)
        .then(response => response.json())
        .then(data => {
            openModal(data);
        })
        .catch(error => console.error('Error:', error));
}

function openModal(id) {
    document.body.style.overflow = 'hidden';
    clearTabClickListeners();
    fetch('/get_sighting/' + id)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok');
            return response.json();
        })
        .then(data => {
            let tabGeneralInfo = document.getElementById('tab-general-info');
            let tabLocationInfo = document.getElementById('tab-location-info');
            let tabUserInfo = document.getElementById('tab-user-info');
            let tabContent = document.getElementById('tab-content');

            // Set initial content
            tabContent.innerHTML = generateGeneralInfo(data);
            setActiveTab(tabGeneralInfo);

            // Add click listeners to tab buttons
            addTabClickListener(tabGeneralInfo, generateGeneralInfo, data);
            addTabClickListener(tabLocationInfo, generateLocationInfo, data);
            addTabClickListener(tabUserInfo, generateUserInfo, data);

            // Show the modal
            document.getElementById('modal').classList.remove('hidden');

            // Disable inputs if the sighting has been approved
            let reportCard = document.querySelector(`[data-report-id="${id}"]`);
            let isApproved = reportCard.getAttribute('data-approved') === 'true';
            disableInputsIfApproved(isApproved);
        })
        .catch(error => console.error('Error:', error));
}


function disableInputsIfApproved(isApproved) {
    let inputs = document.querySelectorAll('.input-field-admin');
    inputs.forEach(input => {
        input.disabled = isApproved;
    });
}


function addTabClickListener(tabElement, contentGenerator, data) {
    let isApproved = document.querySelector(`[data-report-id="${data.id_meldung}"]`).getAttribute('data-approved') === 'true';
    tabElement.onclick = function() {
        if (!this.classList.contains('active')) {
            document.getElementById('tab-content').innerHTML = contentGenerator(data);
            setActiveTab(this);
            disableInputsIfApproved(isApproved);

            if (contentGenerator === generateLocationInfo) {
                initiateMap(data);
            }
        }
    };
}

function clearTabClickListeners() {
    let tabGeneralInfo = document.getElementById('tab-general-info');
    let tabLocationInfo = document.getElementById('tab-location-info');
    let tabUserInfo = document.getElementById('tab-user-info');

    tabGeneralInfo.onclick = null;
    tabLocationInfo.onclick = null;
    tabUserInfo.onclick = null;
}


function initiateMap(data) {
    setTimeout(function () {
        let lat = parseFloat(data.latitude.replace(',', '.'));
        let lng = parseFloat(data.longitude.replace(',', '.'));
        let map = L.map('map').setView([lat, lng], 13);

        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 18,
            tileSize: 512,
            zoomOffset: -1
        }).addTo(map);

        L.marker([lat, lng]).addTo(map);

        // Redraw tiles after the modal is shown
        map.invalidateSize();
    }, 0);
}    

function changeGenderCount(id, type, newCount) {
    fetch(`/change_mantis_count/${id}`, {
        method: 'POST',
        body: new URLSearchParams({ type: type, new_count: newCount }),
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
            } else {
                console.error('Failed to change count:', data.error);
            }
        });
}



function setActiveTab(tab) {
    // Remove 'active' class from all tabs
    let tabs = [document.getElementById('tab-general-info'), document.getElementById('tab-location-info'), document.getElementById('tab-user-info')];
    tabs.forEach(t => t.classList.remove('active'));
    // Add 'active' class to the selected tab
    tab.classList.add('active');
}


function openImageModal(imageUrl) {
    document.body.style.overflow = 'hidden';
    document.getElementById('modalImage').src = imageUrl;
    document.getElementById('imageModal').style.display = 'block';
}

function closeImageModal() {
    document.getElementById('imageModal').style.display = 'none';
    document.body.style.overflow = 'auto';
}

function openImageNewTab() {
    let modalImage = document.getElementById('modalImage');
    window.open(modalImage.src, '_blank');
}

function generateGeneralInfo(data) {
    let mantis_types = ['Männchen', 'Weiblich', 'Nymphe', 'Oothek', 'Andere', 'Anzahl'];
    let gender_counts = [data.art_m, data.art_w, data.art_n, data.art_o, data.art_f, data.tiere];

    let html = `<div class="flex flex-col md:flex-row md:space-x-6">
                    <div class="md:w-1/2">
                        ${mantis_types.map((type, i) => `
                            <div class="flex items-center">
                                <label for="mantis-count-${type}" class="w-32 my-4 mr-2 font-semibold">${type}</label>
                                <input id="mantis-count-${type}" type="number" min="0" value="${gender_counts[i]}" onchange="changeGenderCount(${data.id_meldung}, '${type}', this.value)"
                                    class="input-field-admin" >
                                
                            </div>
                        `).join('')}

                    </div>
                    <div class="space-y-4 md:w-1/2">
                        <p class="mb-4"><strong>Report ID:</strong> ${data.id_meldung}</p>
                        <p class="mb-4"><strong>Date Reported:</strong> ${data.dat_meld.replace(/\d{2}:\d{2}:\d{2} GMT/, '')}</p>
                    </div>
                </div>
                <p class="mt-6 mb-2 font-semibold">Details:</p>
                <div class="px-3 py-2 overflow-auto bg-gray-100 rounded-lg details-text" style="max-height: 150px;">${data.anm_melder.replace(/\n/g, '<br />')}</div>`;
    return html;
}



function generateUserInfo(data) {
    return `<p><strong>User Name:</strong> ${data.user_name}</p>
            <p><strong>User Email:</strong> ${data.user_kontakt}</p>
            <p><strong>User ID:</strong> ${data.user_id}</p>
            <p><strong>User Role:</strong> ${data. user_rolle}</p>`;
}


function generateLocationInfo(data) {
    // Convert location info into HTML string
    return `<p><strong>Location ID:</strong> ${data.fo_zuordnung}</p>
            <div id="map" style="height: 400px; width: 100%;"></div>`;
}


function closeModal() {
    // Hide modal
    document.body.style.overflow = 'auto';
    document.getElementById('modal').classList.add('hidden');
    clearTabClickListeners(); // Clear listeners when the modal is closed
}   

function saveChanges() {
    // Save changes to report details
    // This will require additional setup based on how you want to edit the details
}

// Function to delete a sighting
function deleteSighting(id) {
    let confirmDelete = confirm('Are you sure you want to delete this sighting? This action cannot be undone.');
    if (confirmDelete) {
        fetch('/delete_sighting/' + id, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                // Remove the deleted card from the view
                removeCardFromView(id);
            })
            .catch(error => console.error('Error:', error));
    }
}

function removeCardFromView(id) {
    let card = document.querySelector(`[data-report-id="${id}"]`);
    let followingCards = Array.from(document.querySelectorAll(`[data-report-id]`)).slice(Array.from(document.querySelectorAll(`[data-report-id]`)).indexOf(card) + 1);

    card.classList.add('fade-out');

    // Allow animation to complete before removing the card
    setTimeout(function () {
        card.remove();
        // add slide in animation to following cards
        followingCards.forEach((followingCard) => {
            followingCard.classList.add('slide-in');
            setTimeout(() => {
                followingCard.classList.remove('slide-in');
            }, 500);
        });
    }, 500); // matches the duration of the fade-out animation
}

function exportData(exportType) {
    var exportButton = document.getElementById("dropdownExportButton");
    // Add loading animation to the button
    exportButton.innerHTML = '<svg class="w-5 h-5 mx-auto text-white animate-spin" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24"><circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle><path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path></svg>';
    var url = "/admin/export/xlsx/" + exportType;
    window.location.href = url;

    // Set a timer to reset the button after 5 seconds
    setTimeout(function () {
        exportButton.innerHTML = 'Export<svg class="w-4 h-4 mr-2" xmlns="http://www.w3.org/2000/svg" fill="none" viewbox="0 0 24 24" stroke-width="2" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5" /></svg>';
    }, 5000); // adjust the time as necessary
}


let showApprovedSightings = false;
let showDeletedSightings = false;

function toggleApprovedSightings() {
    var label = document.getElementById("checkbox-label");

    showApprovedSightings = !showApprovedSightings;
    filterSightings();

    label.innerHTML = showApprovedSightings ? "Bestätigt" : "Unbestätigt";
}

function toggleDeletedSightings() {
    var label = document.getElementById("checkbox-label-deleted");

    showDeletedSightings = !showDeletedSightings;
    filterSightings();

    label.innerHTML = showDeletedSightings ? "Gelöscht" : "Nicht gelöscht";
}

// Function to filter sightings based on the toggle state
function filterSightings() {
    let cards = Array.from(document.getElementsByClassName('report-card'));

    cards.forEach(card => {
        let isApproved = card.getAttribute('data-approved') === 'true';
        let isDeleted = card.getAttribute('data-deleted') === 'true';
        let reportId = card.getAttribute('data-report-id');

        // Determine if the card should be shown
        let showCard = true;

        if (showApprovedSightings && !isApproved) {
            showCard = false;
        }

        if (showDeletedSightings && !isDeleted) {
            showCard = false;
        }

        if (!showApprovedSightings && isApproved) {
            showCard = false;
        }

        if (!showDeletedSightings && isDeleted) {
            showCard = false;
        }

        // Hide or show the card based on the final decision
        if (showCard) {
            card.classList.remove('hidden');
        } else {
            card.classList.add('hidden');
        }
    });
}


// Call the filterSightings function initially to apply the default filter
document.addEventListener('DOMContentLoaded', (event) => {
    var label = document.getElementById("checkbox-label");

    if (showApprovedSightings) {
        label.innerHTML = "Bestätigt";
    } else {
        label.innerHTML = "Unbestätigt";
    }

    filterSightings();
});