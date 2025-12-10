window.onload = async function () {
    try {
        // Fetch and update article counts
        await updateArticleStatistics();
        try {
            const response = await fetch(`/api/article/statistic?q=recentArticles`);
            if (response.ok) {
                const result = await response.json();
                const articles = result.result;

                const targetDiv = document.getElementById('recent_articles'); // Replace with your div's id

                articles.forEach(article => {
                    const articleHtml = `
                    
    <li id="${article.uuid}-uuid" class="">
        <div class="flex flex-row">
            <div id="${article.uuid}"
                class="rounded w-full overflow-hidden shadow-lg p-2 mx-auto my-2 flex flex-row justify-between
                                    hover:text-teal-100 hover:bg-teal-900 ease-in duration-100 border dark:border-gray-300">
                <div class="text-left">
                    ${article.field !== "tittle" ? `${article.title}<br />` : ""}
                    ${article.authors.map(author => author.fullName).join("; ")}<br />
                    <span class="italic">${article.journal || ''}</span><br />
                    ${article.publication_date || ''} ${article.journal_volume || ''}(${article.journal_issue ||
                        ''}):${article.pages || ''}<br />
                    ${article.doi ? `DOI: <a href="https://doi.org/${article.doi}" target="_blank">${article.doi}</a>` :
                            ''}
                    ${article.pubmed_id ? `PUBMED: <a href="https://pubmed.ncbi.nlm.nih.gov/${article.pubmed_id}"
                        target="_blank">${article.pubmed_id}</a>` : ''}
                    ${article.created_at ? `Created at: ${article.created_at}` : ''}
                </div>
                <div class="p-2 flex flex-col align-middle gap-2">
                    <a href="/article/${article.uuid}" target="_blank">
                        <svg width="24px" height="24px" viewBox="0 0 1024 1024" class="icon" version="1.1"
                                        xmlns="http://www.w3.org/2000/svg">
                                        <path
                                            d="M94.433 536.378c49.818-67.226 110.761-124.854 180.172-166.808 35.333-21.356 62.64-33.686 99.016-45.698 17.076-5.638 34.511-10.135 52.088-13.898 23.033-4.932 28.596-5.483 49.577-7.228 76.233-6.333 138.449 4.648 210.869 33.643 3.581 1.435 10.361 4.513 18.987 8.594 8.488 4.013 16.816 8.358 25.086 12.801 18.349 9.861 36.004 20.974 53.173 32.756 31.245 21.442 62.37 49.184 91.227 79.147 20.218 20.991 39.395 43.706 56.427 66.689 14.436 19.479 38.301 29.282 60.985 15.991 19.248-11.276 30.491-41.417 15.991-60.984-101.194-136.555-243.302-247.3-415.205-272.778-165.834-24.575-325.153 31.855-452.148 138.262-46.849 39.252-86.915 85.525-123.221 134.518-14.5 19.567-3.258 49.708 15.991 60.984 22.685 13.291 46.549 3.488 60.985-15.991z"
                                            fill="currentColor" />
                                        <path
                                            d="M931.055 491.378c-49.817 67.228-110.761 124.856-180.173 166.811-35.332 21.354-62.639 33.684-99.015 45.694-17.076 5.641-34.512 10.137-52.09 13.902-23.032 4.931-28.593 5.48-49.576 7.225-76.233 6.336-138.449-4.648-210.869-33.642-3.582-1.436-10.362-4.514-18.987-8.595-8.488-4.015-16.816-8.357-25.087-12.801-18.348-9.862-36.003-20.974-53.172-32.755-31.245-21.443-62.37-49.184-91.227-79.149-20.218-20.99-39.395-43.705-56.427-66.69-14.436-19.479-38.3-29.279-60.985-15.991-19.249 11.276-30.491 41.419-15.991 60.984C118.65 672.929 260.76 783.677 432.661 809.15c165.834 24.578 325.152-31.854 452.148-138.259 46.85-39.256 86.915-85.528 123.222-134.521 14.5-19.564 3.257-49.708-15.991-60.984-22.685-13.287-46.55-3.487-60.985 15.992z"
                                            fill="#C45FA0" />
                                        <path
                                            d="M594.746 519.234c0.03 46.266-34.587 83.401-80.113 85.188-46.243 1.814-83.453-35.93-85.188-80.11-0.953-24.271-19.555-44.574-44.574-44.574-23.577 0-45.527 20.281-44.573 44.574 3.705 94.378 79.154 169.32 174.334 169.258 94.457-0.063 169.321-81.897 169.261-174.335-0.039-57.486-89.184-57.49-89.147-0.001z"
                                            fill="#F39A2B" />
                                        <path
                                            d="M430.688 514.818c0.876-45.416 37.262-81.797 82.677-82.672 45.438-0.875 81.824 38.571 82.673 82.672 1.105 57.413 90.256 57.521 89.147 0-1.827-94.791-77.028-169.994-171.82-171.82-94.787-1.827-170.049 79.785-171.824 171.82-1.108 57.522 88.04 57.413 89.147 0z"
                                            fill="#E5594F" />
                                    </svg>
                    </a>
                   
                </div>
            </div>
        </div>
    </li>

        `;
                    targetDiv.insertAdjacentHTML('beforeend', articleHtml);
                });


            }
        } catch (error) {
            console.error(`Error fetching statistic: ${query}`, error);
        }

    } catch (error) {
        console.error("Error in window.onload:", error);
    }
};

async function updateArticleStatistics() {
    const endpoints = [
        { id: "article_count", query: "count" },
        { id: "article_view_count", query: "view" },
        { id: "article_current_count", query: "currentCount" },
    ];

    // Fetch counts and update elements
    for (const { id, query } of endpoints) {
        try {
            const response = await fetch(`/api/article/statistic?q=${query}`);
            if (response.ok) {
                const result = await response.json();
                document.getElementById(id).innerHTML = result.result;
            }
        } catch (error) {
            console.error(`Error fetching statistic: ${query}`, error);
        }
    }

    // Fetch and process word cloud data
    try {
        const responseWord = await fetch('/api/article/statistic?q=keyword');
        if (responseWord.ok) {
            const result = await responseWord.json();
            const myWords = result.result;
            // console.log(myWords);            
            createWordCloud(myWords);

        }
    } catch (error) {
        console.error("Error fetching word cloud data:", error);
    }
}

document.addEventListener("DOMContentLoaded", async function () {
    try {
        const response = await fetch('/api/article/statistic?q=yearData');
        const data = await response.json();

        const labels = data.labels || []; // X-axis labels
        const values = data.values || []; // Y-axis values

        // Initialize the chart with fetched data
        createAreaChart(labels, values);
    } catch (error) {
        console.error("Error fetching year data:", error);
    }
});

function createWordCloud(myWords) {
    if (!Array.isArray(myWords) || myWords.length === 0) {
        console.error("No words provided for the word cloud.");
        return;
    }

    // Screen size-based logic
    const screenWidth = window.innerWidth;
    const wordCount = screenWidth <= 768 ? 25 : screenWidth <= 1200 ? 50 : 100;
    const selectedWords = myWords.slice(0, Math.min(wordCount, myWords.length));

    const margin = { top: 10, right: 20, bottom: 10, left: 20 },
        width = Math.min(screenWidth, 1200) - margin.left - margin.right,
        height = Math.min(window.innerHeight, 500) - margin.top - margin.bottom;

    // Clear existing SVG
    d3.select("#my_dataviz").html("");

    const svg = d3.select("#my_dataviz").append("svg")
        .attr("width", width)
        .attr("height", height + margin.top + margin.bottom)
        .append("g")
        .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Font size scaling
    const maxWordSize = Math.max(...selectedWords.map(d => d.size));
    const minWordSize = Math.min(...selectedWords.map(d => d.size));
    const scaleFontSize = d3.scaleLinear()
        .domain([minWordSize, maxWordSize])
        .range([10, Math.min(width, height) / 10]);

    if (isNaN(maxWordSize) || isNaN(minWordSize)) {
        console.error("Invalid word sizes detected. Please verify your data.");
        return;
    }

    // Create layout
    const layout = d3.layout.cloud()
        .size([width, height])
        .words(selectedWords.map(d => ({
            text: d.word,  // Word text
            size: scaleFontSize(d.size),  // Scaled font size
            url: d.url,  // Optional URL for the word
        })))
        .padding(5)
        .rotate(() => (Math.random() < 0.5 ? 0 : 90))
        .spiral("archimedean")
        .fontSize(d => d.size)
        .on("end", draw);

    layout.start();

    function draw(words) {
        svg.append("g")
            .attr("transform", `translate(${layout.size()[0] / 2},${layout.size()[1] / 2})`)
            .selectAll("text")
            .data(words)
            .enter().append("text")
            .style("font-size", d => `${d.size}px`)
            .style("fill", () => d3.interpolateRainbow(Math.random()))
            .attr("text-anchor", "middle")
            .style("font-family", "Impact")
            .attr("transform", d => `translate(${d.x},${d.y})rotate(${d.rotate})`)
            .text(d => d.text)  // Use the text for display
            .on("click", function (event, d) {
                if (event.url) {
                    window.open(event.url, "_blank");  // Open the URL in a new tab
                } else {
                    console.warn("No URL provided for this word.");
                }
            })
            .style("cursor", "pointer"); // Change cursor to pointer for clickable words
    }

    // Handle window resize
    d3.select(window).on("resize", () => {
        d3.select("#my_dataviz").html("");
        createWordCloud(myWords);
    });
}


// Function to create the area chart
function createAreaChart(labels, values) {
    const options = {
        chart: {
            height: "80%",
            type: "area",
            fontFamily: "Inter, sans-serif",
            dropShadow: { enabled: false },
            toolbar: { show: false },
        },
        tooltip: {
            enabled: true,
            x: { show: false },
        },
        fill: {
            type: "gradient",
            gradient: {
                opacityFrom: 0.55,
                opacityTo: 0,
                shade: "#1C64F2",
                gradientToColors: ["#1C64F2"],
            },
        },
        dataLabels: { enabled: false },
        stroke: { width: 6 },
        grid: {
            show: false,
            strokeDashArray: 4,
            padding: { left: 2, right: 2, top: 0, bottom: 2 },
        },
        series: [{
            name: "Articles",
            data: values,
            color: "#1A56DB",
        }],
        xaxis: {
            categories: labels,
            labels: { show: false },
            axisBorder: { show: false },
            axisTicks: { show: false },
        },
        yaxis: { show: false },
    };

    if (document.getElementById("area-chart") && typeof ApexCharts !== 'undefined') {
        const chart = new ApexCharts(document.getElementById("area-chart"), options);
        chart.render();
    }
}
