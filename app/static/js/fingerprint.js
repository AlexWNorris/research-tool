// 1. FingerprintJS Loading
const fpPromise = import('https://openfpcdn.io/fingerprintjs/v5')
    .then(FingerprintJS => FingerprintJS.load());

// 2. Function to build and display the table
function displayAttributes(attributesList) {
    const tableBody = document.querySelector('#attributesTable tbody');
    
    // Clear existing rows if any
    tableBody.innerHTML = '';

    for (const key in attributesList) {
        if (attributesList.hasOwnProperty(key)) {
            const component = attributesList[key];
            const row = tableBody.insertRow();
            
            // Column 1: Attribute Name
            const cellName = row.insertCell(0);
            cellName.textContent = key;
            
            // Column 2: Value
            const cellValue = row.insertCell(1);
            // Handle complex values (like objects/arrays) by stringifying them
            if (typeof component.value === 'object' && component.value !== null) {
                cellValue.textContent = JSON.stringify(component.value);
            } else {
                cellValue.textContent = component.value;
            }
        }
    }
}

// 3. Scroll Functions (linked to the arrow buttons)
function scrollToTop() {
    document.getElementById('tableContainer').scrollTop = 0;
}

function scrollToBottom() {
    const container = document.getElementById('tableContainer');
    container.scrollTop = container.scrollHeight;
}

// 4. Initialize logic when the DOM is fully loaded
document.addEventListener('DOMContentLoaded', () => {
    // Get Attributes and populate table
    fpPromise
        .then(fp => fp.get({ extendedResult: true }))
        .then(result => {
            const attributesList = result.components;
            displayAttributes(attributesList);
            
            // Attach event listener to consent button
            document.getElementById('consentButton').addEventListener('click', () => {
                console.log('Consent given! Sending data:', {
                    visitorId: result.visitorId,
                    components: attributesList
                });
                alert('Consent registered! Check console for data being sent.');
            });
        })
        .catch(error => {
            console.error('Error loading FingerprintJS:', error);
            const tableBody = document.querySelector('#attributesTable tbody');
            const row = tableBody.insertRow();
            row.insertCell(0).textContent = 'Error';
            row.insertCell(1).textContent = 'Failed to load attributes.';
        });
});