document.addEventListener("DOMContentLoaded", function(){
  // Load comments when the page is ready
  loadComments();

  // Attach event to the comment button
  document.getElementById("commentButton").addEventListener("click", function(){
    submitComment();
  });

  document.getElementById("pastCommentsButton").addEventListener("click", loadPastComments);

  // Function to submit a new comment
  function submitComment(){
    var content = document.getElementById("comment-input").value;
    if(content){ // Check if the comment is not empty
      // Perform the AJAX request
      fetch('/submit_comment', {
        method: 'POST',
        body: JSON.stringify({content: content}),
        headers: {
          'Content-Type': 'application/json'
        }
      })
      .then(response => response.json())
      .then(data => {
        if(data.success){
          // Clear the input field and reload comments
          document.getElementById("comment-input").value = '';
          loadComments();
        }
      });
    }
  }

  // Function to load and display comments
  function loadComments(){
    fetch('/get_comments')
      .then(response => response.json())
      .then(data => {
        var commentsContainer = document.getElementById("comment-container");
        commentsContainer.innerHTML = ''; // Clear existing comments
        data.comments.forEach(function(comment){
          var commentDiv = document.createElement("div");
          commentDiv.className = "comment";
          commentDiv.textContent = comment.content;
          commentsContainer.appendChild(commentDiv);
        });
      });
  }
  
  function loadPastComments() {
    fetch('/get_past_comments')
      .then(response => response.json())
      .then(data => {
        var commentsContainer = document.getElementById("comment-container");
        commentsContainer.innerHTML = ''; // Clear existing comments
        data.past_comments.forEach(function(comment){
          var commentDiv = document.createElement("div");
          commentDiv.className = "past-comment";
          commentDiv.textContent = comment.content;
          commentsContainer.appendChild(commentDiv);
        });
      });
  }
  


  // Function to load past comments - This will be implemented later
  // document.getElementById("pastComments").addEventListener("click", function(){
  //   // Logic to fetch and display past comments
  // });
});
