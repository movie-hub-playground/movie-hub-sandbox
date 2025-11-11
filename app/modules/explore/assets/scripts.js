document.addEventListener('DOMContentLoaded', () => {
    send_query();
});

function send_query() {

    console.log("send query...")

    document.getElementById('results').innerHTML = '';
    document.getElementById("results_not_found").style.display = "none";
    console.log("hide not found icon");

    const filters = document.querySelectorAll('#filters input, #filters select, #filters [type="radio"]');

    filters.forEach(filter => {
        filter.addEventListener('input', () => {
            const csrfToken = document.getElementById('csrf_token').value;

            const searchCriteria = {
                csrf_token: csrfToken,
                query: document.querySelector('#query').value,
                publication_type: document.querySelector('#publication_type').value,
                sorting: document.querySelector('[name="sorting"]:checked').value,
            };

            console.log(document.querySelector('#publication_type').value);

            fetch('/explore', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(searchCriteria),
            })
                .then(response => response.json())
                .then(data => {

                    console.log(data);
                    document.getElementById('results').innerHTML = '';

                    // results counter - ADAPTADO PARA MOVIE DATASETS
                    const resultCount = data.length;
                    const resultText = resultCount === 1 ? 'movie dataset' : 'movie datasets';
                    document.getElementById('results_number').textContent = `${resultCount} ${resultText} found`;

                    if (resultCount === 0) {
                        console.log("show not found icon");
                        document.getElementById("results_not_found").style.display = "block";
                    } else {
                        document.getElementById("results_not_found").style.display = "none";
                    }

                    // RENDERIZAR MOVIE DATASETS
                    data.forEach(dataset => {
                        let card = document.createElement('div');
                        card.className = 'col-12';
                        card.innerHTML = `
                            <div class="card">
                                <div class="card-body">
                                    <div class="d-flex align-items-center justify-content-between">
                                        <h3><a href="${dataset.url}">🎬 ${dataset.title}</a></h3>
                                        <div>
                                            <span class="badge bg-primary">${dataset.movies_count || 0} ${dataset.movies_count === 1 ? 'movie' : 'movies'}</span>
                                            <span class="badge bg-secondary" style="cursor: pointer;" onclick="set_publication_type_as_query('${dataset.publication_type}')">${dataset.publication_type}</span>
                                        </div>
                                    </div>
                                    <p class="text-secondary">${formatDate(dataset.created_at)}</p>

                                    <div class="row mb-2">
                                        <div class="col-md-4 col-12">
                                            <span class="text-secondary">
                                                Description
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            <p class="card-text">${dataset.description}</p>
                                        </div>
                                    </div>

                                    <div class="row mb-2">
                                        <div class="col-md-4 col-12">
                                            <span class="text-secondary">
                                                Authors
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            ${dataset.authors.map(author => `
                                                <p class="p-0 m-0">${author.name}${author.affiliation ? ` (${author.affiliation})` : ''}${author.orcid ? ` (${author.orcid})` : ''}</p>
                                            `).join('')}
                                        </div>
                                    </div>

                                    <div class="row mb-2">
                                        <div class="col-md-4 col-12">
                                            <span class="text-secondary">
                                                Tags
                                            </span>
                                        </div>
                                        <div class="col-md-8 col-12">
                                            ${dataset.tags.map(tag => `<span class="badge bg-primary me-1" style="cursor: pointer;" onclick="set_tag_as_query('${tag}')">${tag}</span>`).join('')}
                                        </div>
                                    </div>

                                    <div class="row">
                                        <div class="col-md-4 col-12">
                                        </div>
                                        <div class="col-md-8 col-12">
                                            <a href="${dataset.url}" class="btn btn-outline-primary btn-sm" style="border-radius: 5px;">
                                                <i data-feather="eye"></i> View movie library
                                            </a>
                                            <a href="/movie/dataset/download/${dataset.id}" class="btn btn-outline-secondary btn-sm" style="border-radius: 5px;">
                                                <i data-feather="download"></i> Download (${dataset.total_size_in_human_format})
                                            </a>
                                        </div>
                                    </div>

                                </div>
                            </div>
                        `;

                        document.getElementById('results').appendChild(card);
                    });

                    if (typeof feather !== 'undefined') {
                        feather.replace();
                    }
                });
        });
    });
}

function formatDate(dateString) {
    const options = {day: 'numeric', month: 'long', year: 'numeric', hour: 'numeric', minute: 'numeric'};
    const date = new Date(dateString);
    return date.toLocaleString('en-US', options);
}

function set_tag_as_query(tagName) {
    const queryInput = document.getElementById('query');
    queryInput.value = tagName.trim();
    queryInput.dispatchEvent(new Event('input', {bubbles: true}));
}

function set_publication_type_as_query(publicationType) {
    const publicationTypeSelect = document.getElementById('publication_type');
    for (let i = 0; i < publicationTypeSelect.options.length; i++) {
        if (publicationTypeSelect.options[i].text === publicationType.trim()) {
            publicationTypeSelect.value = publicationTypeSelect.options[i].value;
            break;
        }
    }
    publicationTypeSelect.dispatchEvent(new Event('input', {bubbles: true}));
}

document.getElementById('clear-filters').addEventListener('click', clearFilters);

function clearFilters() {
    // Reset the search query
    let queryInput = document.querySelector('#query');
    queryInput.value = "";

    // Reset the publication type to its default value
    let publicationTypeSelect = document.querySelector('#publication_type');
    publicationTypeSelect.value = "any";

    // Reset the sorting option
    let sortingOptions = document.querySelectorAll('[name="sorting"]');
    sortingOptions.forEach(option => {
        option.checked = option.value == "newest";
    });

    // Perform a new search with the reset filters
    queryInput.dispatchEvent(new Event('input', {bubbles: true}));
}

document.addEventListener('DOMContentLoaded', () => {
    let urlParams = new URLSearchParams(window.location.search);
    let queryParam = urlParams.get('query');

    if (queryParam && queryParam.trim() !== '') {
        const queryInput = document.getElementById('query');
        queryInput.value = queryParam
        queryInput.dispatchEvent(new Event('input', {bubbles: true}));
        console.log("throw event");
    } else {
        const queryInput = document.getElementById('query');
        queryInput.dispatchEvent(new Event('input', {bubbles: true}));
    }
});