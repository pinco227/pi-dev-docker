/**
* Display bootstrap spinner by creating element and appending it to body
*/
const showSpinner = () => {
    const overlay = Object.assign(document.createElement('div'), {
        id: "spin-overlay"
    });
    const spinnerEl = Object.assign(document.createElement('div'), {
        id: "spinner",
        className: 'spinner-border',
        innerHTML: `<span class="visually-hidden">Loading...</span>`
    });
    document.body.appendChild(overlay);
    document.body.appendChild(spinnerEl);
}

/**
* Hides previously created spinner by removing element
*/
const hideSpinner = () => {
    const overlay = document.getElementById("spin-overlay");
    const spinner = document.getElementById("spinner");

    if (overlay) overlay.remove();
    if (spinner) spinner.remove();
}

/**
* Sets the value bubble for the range input.
* @param {obj} range - range DOM element
* @param {obj} bubble - bubble DOM element
*/
const setBubble = (range, bubble) => {
    const val = range.value;
    const min = range.min ? range.min : 0;
    const max = range.max ? range.max : 100;
    const newVal = Number(((val - min) * 100) / (max - min));
    bubble.innerHTML = val;

    // Sorta magic numbers based on size of the native UI thumb
    bubble.style.left = `calc(${newVal}% + (${8 - newVal * 0.15}px))`;
}

// Make value bubble for range inputs
// CREDIT: https://css-tricks.com/value-bubbles-for-range-inputs/
const allRanges = document.querySelectorAll(".range-wrap");
allRanges.forEach(wrap => {
    const range = wrap.querySelector(".range");
    const bubble = wrap.querySelector(".bubble");

    range.addEventListener("input", () => {
        setBubble(range, bubble);
    });
    setBubble(range, bubble);
});

// Initialize bootstrap tooltips
const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
const tooltipList = tooltipTriggerList.map(tooltipTriggerEl => {
    return new bootstrap.Tooltip(tooltipTriggerEl);
});