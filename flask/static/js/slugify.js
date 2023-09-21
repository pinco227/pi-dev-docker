/** 
* @credit https://gist.github.com/mathewbyrne/1280286
* @summary Transform a string to a url-friendly slug version
* @param {string} text - Input string
* @return {string} Returns the slug of the input string
*/
const slugify = (text) => {
    return text.toString().toLowerCase()
        .replace(/\s+/g, '-')           // Replace spaces with -
        .replace(/[^\w\-]+/g, '')       // Remove all non-word chars
        .replace(/\-\-+/g, '-')         // Replace multiple - with single -
        .replace(/^-+/, '')             // Trim - from start of text
        .replace(/-+$/, '');            // Trim - from end of text
}

//Declare used variables
const srcElement = document.getElementById('title');
const targetElement = document.getElementById('slug');

// Input event listener
srcElement.addEventListener('input', () => {
    targetElement.value = slugify(srcElement.value);
})