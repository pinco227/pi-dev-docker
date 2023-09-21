// Initialize tiny rich text editor
tinymce.init({
    selector: '#body',
    plugins: 'anchor autolink link image table spellchecker lists autoresize charmap code emoticons fullscreen help hr media paste preview print quickbars toc',
    contextmenu: 'anchor link image table spellchecker lists',
    toolbar: 'undo redo | styleselect | bold italic underline | alignleft aligncenter alignright alignjustify | numlist bullist | emoticons | code preview fullscreen',
    toolbar_mode: 'wrap',
    quickbars_insert_toolbar: false,
    min_height: 300,
    max_height: 500,
    paste_as_text: true,
    relative_urls: false,
    content_css: '/static/css/style.css',
    content_style: 'body { background-color: #fffcf6; }',
    image_list: (success) => {
        success(getPhotoList());
    }
});