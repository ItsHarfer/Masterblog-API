/**
 * main.js
 *
 * This script initializes and manages the interactive behavior of the Masterblog frontend.
 * It handles dynamic loading of posts, user interactions (likes, comments), 
 * and communicates with the backend API via fetch requests.
 *
 * Features:
 * - Fetch and render posts from the /api/posts endpoint
 * - Handle like and comment actions with POST requests
 * - Provide visual feedback and update the DOM dynamically
 *
 * Dependencies:
 * - Vanilla JavaScript (no external libraries required)
 * - Assumes an HTML structure (index.html) with elements for displaying posts and capturing input
 *
 * Author: Martin Haferanke
 * Date: 2025-06-30
 */

// Function that runs once the window is fully loaded
window.onload = function () {
    /**
     * Initialize the page by loading saved API base URL and loading posts if available.
     */
    let savedBaseUrl = localStorage.getItem('apiBaseUrl');
    if (savedBaseUrl) {
        document.getElementById('api-base-url').value = savedBaseUrl;
        loadPosts();
    }
}

/**
 * Render a single post element.
 * @param {Object} post - The post object containing post data.
 * @returns {HTMLElement} The DOM element representing the post.
 */
function renderPost(post) {
    const postDiv = document.createElement('div');
    postDiv.className = 'post';
    postDiv.innerHTML = `
        <div class="post-header">
            <h2>${post.title}</h2>
            <div class="post-actions">
                <button class="like-button" onclick="likePost(${post.id})">❤️ (<span id="likes-button-${post.id}">${post.likes || 0}</span>) Like</button>
                <button class="comment-button" onclick="toggleComments(${post.id})">💬 Comments (<span id="comment-count-${post.id}">${post.comments?.length || 0}</span>)</button>
                <button class="edit-button" onclick="editPost(${post.id})">✏️ Edit</button>
                <button class="delete-button" onclick="confirmDelete(${post.id})">🗑 Delete</button>
            </div>
        </div>
        <div class="post-meta">
            <span><strong>Author:</strong> ${post.author || 'Unknown'}</span>
            <span><strong>Date:</strong> ${post.date || 'N/A'}</span>
        </div>
        <p>${post.content}</p>
        <div class="post-comments-toggle"></div>
        <div class="comments-section" id="comments-${post.id}" style="display:none;">
            <div class="comments-list" id="comments-list-${post.id}">
                ${(post.comments || []).map(comment => `<div class="comment">${comment}</div>`).join('')}
            </div>
            <textarea id="comment-input-${post.id}" placeholder="Write a comment..." class="styled-textarea"></textarea>
            <button class="btn" onclick="submitComment(${post.id})" style="color: white">Submit Comment</button>
        </div>`;
    return postDiv;
}

/**
 * Search posts by a term in title, content, author, or date.
 * Fetches filtered posts from the API and updates the post container.
 */
function searchPosts() {
    let baseUrl = document.getElementById('api-base-url').value;
    let term = document.getElementById('search-term').value;

    // Fetch posts filtered by the search term on multiple fields
    fetch(`${baseUrl}/posts/search?title=${term}&content=${term}&author=${term}&date=${term}`)
        .then(response => response.json())
        .then(data => {
            const postContainer = document.getElementById('post-container');
            // Clear current posts before adding filtered results
            postContainer.innerHTML = '';
            data.forEach(post => {
                const postDiv = renderPost(post);
                postContainer.appendChild(postDiv);
            });
            showToast(`🔍 Filtered posts by: "${term}". Blog list updated.`);
        })
        .catch(error => console.error('Search error:', error));
}

/**
 * Load posts from the API with optional sorting.
 * Updates the UI with the posts or shows connection warning on failure.
 * @param {boolean} [showLoadToast=true] - Whether to show a toast notification after loading.
 */
function loadPosts(showLoadToast = true) {
    let baseUrl = document.getElementById('api-base-url').value;
    localStorage.setItem('apiBaseUrl', baseUrl);
    let sort = document.getElementById('sort-field')?.value || 'date';
    let direction = document.getElementById('sort-direction')?.value || 'asc';
    let queryParams = `?sort=${sort}&direction=${direction}`;

    // Fetch posts from the API with sorting parameters
    fetch(baseUrl + '/posts' + queryParams)
        .then(response => {
            if (!response.ok) throw new Error('API unavailable');
            return response.json();
        })
        .then(data => {
            const sectionBlocks = document.querySelectorAll('.top-bar .section-block');
            sectionBlocks.forEach(block => {
                block.classList.remove('disabled-card');
            });

            document.getElementById('connection-warning').style.display = 'none';

            const postContainer = document.getElementById('post-container');
            // Clear current posts before adding new ones
            postContainer.innerHTML = '';

            data.forEach(post => {
                const postDiv = renderPost(post);
                postContainer.appendChild(postDiv);
            });
            if (showLoadToast) {
                showToast("🔄 Blog list updated.");
            }
        })
        .catch(error => {
            console.error('Error:', error);
            const sectionBlocks = document.querySelectorAll('.top-bar .section-block:not(:first-child)');
            sectionBlocks.forEach(block => {
                block.classList.add('disabled-card');
            });
            document.getElementById('connection-warning').style.display = 'block';
        });
}

/**
 * Toggle the visibility of the comments section for a specific post.
 * @param {number} postId - The ID of the post.
 */
function toggleComments(postId) {
    const commentSection = document.getElementById(`comments-${postId}`);
    commentSection.style.display = commentSection.style.display === 'none' ? 'block' : 'none';
}

/**
 * Submit a new comment for a post.
 * Sends the comment to the API and updates the comment list on success.
 * @param {number} postId - The ID of the post to comment on.
 */
function submitComment(postId) {
    const baseUrl = document.getElementById('api-base-url').value;
    const textarea = document.getElementById(`comment-input-${postId}`);
    const comment = textarea.value.trim();
    if (!comment) return;

    // Post new comment to the API for the specified post
    fetch(`${baseUrl}/posts/${postId}/comment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ comment })
    })
    .then(response => response.json())
    .then(data => {
      const list = document.getElementById(`comments-list-${postId}`);
      const countSpan = document.getElementById(`comment-count-${postId}`);
      const div = document.createElement('div');
      div.className = 'comment';
      div.textContent = comment;
      list.appendChild(div);
      textarea.value = '';
      countSpan.textContent = data.post.comments.length;
    })
    .catch(error => console.error('Comment error:', error));
}

/**
 * Add a new post by sending post data to the API.
 * Then reloads the posts list.
 */
function addPost() {
    let baseUrl = document.getElementById('api-base-url').value;
    let postTitle = document.getElementById('post-title').value;
    let postContent = document.getElementById('post-content').value;
    let postAuthor = document.getElementById('post-author').value;

    // Send new post data to the API to create a post
    fetch(baseUrl + '/posts', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
            title: postTitle,
            content: postContent,
            author: postAuthor,
            date: new Date().toISOString().split('T')[0]
        })
    })
        .then(response => response.json())
        .then(post => {
            console.log('Post added:', post);
            showToast("📘Post successfully added!");
            loadPosts(false);
        })
        .catch(error => console.error('Error:', error));
}

/**
 * Delete a post by ID by sending a DELETE request to the API.
 * Then reloads the posts list.
 * @param {number} postId - The ID of the post to delete.
 */
function deletePost(postId) {
    let baseUrl = document.getElementById('api-base-url').value;

    fetch(baseUrl + '/posts/' + postId, {
        method: 'DELETE'
    })
        .then(response => {
            console.log('Post deleted:', postId);
            showToast("🗑️ Post deleted successfully.");
            loadPosts(false);
        })
        .catch(error => console.error('Error:', error));
}

/**
 * Enter edit mode for a post, replacing the post content with editable inputs.
 * @param {number} postId - The ID of the post to edit.
 */
function editPost(postId) {
    const postDiv = document.querySelector(`.post button[onclick="editPost(${postId})"]`).closest('.post');
    const title = postDiv.querySelector('h2')?.textContent || '';
    const content = postDiv.querySelector('p')?.textContent || '';
    const author = postDiv.querySelector('span')?.textContent.replace(/^Author:\s*/, '') || '';

    postDiv.innerHTML = `
        <label for="edit-title-${postId}">Title</label>
        <input type="text" class="styled-input" id="edit-title-${postId}" value="${title}" placeholder="Title" />
        <label for="edit-content-${postId}">Content</label>
        <textarea class="styled-textarea" id="edit-content-${postId}" placeholder="Content">${content}</textarea>
        <label for="edit-author-${postId}">Author</label>
        <input type="text" class="styled-input" id="edit-author-${postId}" value="${author}" placeholder="Author" />
        <div class="button-row"> 
            <button class="btn" onclick="updatePost(${postId})" style="color: white">Update</button>
            <button class="btn" onclick="loadPosts(false)" style="color: white">Cancel</button>
        </div>
    `;
}

/**
 * Update a post by sending updated data to the API.
 * Then reloads the posts list.
 * @param {number} postId - The ID of the post to update.
 */
function updatePost(postId) {
    const baseUrl = document.getElementById('api-base-url').value;
    const title = document.getElementById(`edit-title-${postId}`).value;
    const content = document.getElementById(`edit-content-${postId}`).value;
    const author = document.getElementById(`edit-author-${postId}`).value;

    // Send updated post data to the API
    fetch(`${baseUrl}/posts/${postId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ title, content, author })
    })
    .then(response => response.json())
    .then(() => {
        showToast("✏️ Post updated successfully.");
        loadPosts(false);
    })
    .catch(error => console.error('Update error:', error));
}

/**
 * Confirm deletion of a post with the user before proceeding.
 * @param {number} postId - The ID of the post to delete.
 */
function confirmDelete(postId) {
    if (window.confirm("Are you sure you want to delete this post?")) {
        deletePost(postId);
    }
}

/**
 * Show a temporary toast notification with a message.
 * @param {string} message - The message to display in the toast.
 */
function showToast(message) {
    const toast = document.getElementById("toast");
    toast.textContent = message;
    toast.style.visibility = "visible";
    toast.style.opacity = "1";
    toast.style.bottom = "30px";

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.bottom = "0";
        setTimeout(() => {
            toast.style.visibility = "hidden";
        }, 600);
    }, 3000);
}

/**
 * Like a post by sending a POST request to the API.
 * Updates the likes count in the UI on success.
 * @param {number} postId - The ID of the post to like.
 */
function likePost(postId) {
    let baseUrl = document.getElementById('api-base-url').value;
    fetch(`${baseUrl}/posts/${postId}/like`, {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        document.getElementById(`likes-button-${postId}`).textContent = data.post.likes;
        showToast("❤️ Post liked!");
    })
    .catch(error => console.error('Like error:', error));
}
