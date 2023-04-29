def javascript():
    return """
    <script>

function waitForImage(uuidValue) {
  // Wait until image is done
  $.ajax({
    type: 'POST',
    url: '/get_jobs',
    contentType: 'application/json; charset=utf-8',
    dataType:'json',
    data: JSON.stringify({'api_key': 'demo', 'uuid': uuidValue}),
    success: function(response) {
        console.log(response);
        $('#newjobresult').html('<p>waiting for result...<p>');
        if (response.jobs.length == 1) {
            if (response.jobs[0].status == "done") {
                $('#newjobresultimg').attr('src', response.jobs[0].img);
                return;
            } else {
                $('#newjobresult').append("<p>current status: " + response.jobs[0].status + "</p>")
            }
        }
        setTimeout(waitForImage, 1000);  // refresh every second
    },
    error: function(xhr, status, error) {
        // Handle error response
        console.log(xhr.responseText);
    }
  });
}

$( document ).ready(function() {
  console.log( "--- csrf token set ---" );

  var csrftoken = $("[name=csrfmiddlewaretoken]").val();
  function csrfSafeMethod(method) {
      // these HTTP methods do not require CSRF protection
      return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
  }
  $.ajaxSetup({
      beforeSend: function(xhr, settings) {
          if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
              xhr.setRequestHeader("X-CSRFToken", csrftoken);
          }
      }
  });

  $('#newjob').click(function(e) {
    e.preventDefault(); // Prevent the default form submission

    // Gather input field values
    var promptVal = $('#prompt').val();
    var negPromptVal = $('#negprompt').val();

    if (promptVal == "") {
        alert("needs to write a prompt!");
        return;
    }

    // Send POST request using Ajax
    $.ajax({
      type: 'POST',
      url: '/add_job',
      contentType: 'application/json; charset=utf-8',
      dataType:'json',
      data: JSON.stringify({'api_key': 'demo', 'prompt': promptVal, 'neg_prompt': negPromptVal}),
      success: function(response) {
        console.log(response);
        if (response.uuid) {
            $('#jobuuid').val(response.uuid);
        }
        waitForImage(response.uuid);
      },
      error: function(xhr, status, error) {
        // Handle error response
        console.log(xhr.responseText);
      }
    });
  });


});
</script>
    """

def stylesheet():
    return """
    """

def content():
    return """
    <form>
  <div class="mb-3">
    <label for="prompt" class="form-label">Prompt</label>
    <input type="prompt" class="form-control" id="prompt" aria-describedby="promptHelp">
    <div id="promptHelp" class="form-text">Less than 77 words otherwise it'll be truncated</div>
  </div>
  <div class="mb-3">
    <label for="negprompt" class="form-label">Negative Prompt</label>
    <input type="negprompt" class="form-control" id="negprompt" aria-describedby="negpromptHelp">
    <div id="negpromptHelp" class="form-text">Less than 77 words otherwise it'll be truncated</div>
  </div>
  <button id="newjob" type="submit" class="btn btn-primary">Submit New Job</button>
</form>

<div class="card mb-3">
<div class="card-body" id="newjobresult"></div>
<img id="newjobresultimg" class="card-img-bottom" />
</div>

<form>
  <div class="mb-3">
    <label for="jobuuid" class="form-label">Job UUID</label>
    <input type="jobuuid" class="form-control" id="jobuuid" aria-describedby="">
  </div>
  <button id="getjob" type="submit" class="btn btn-primary">Get Jobs</button>
  <button id="canceljob" type="submit" class="btn btn-primary">Cancel Job</button>
</form>

<div class="mb-3" id="joblist">
</div>
    """

def web():
    return """
<html lang="en">

<head>
  <meta charset="utf-8">

  <title>Happy Diffusion (Private Access) | 9pm</title>
  <meta name="description" content="Stable Diffusion Online">
  <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">

  <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/css/bootstrap.min.css" rel="stylesheet"
    integrity="sha384-Zenh87qX5JnK2Jl0vWa8Ck2rdkQ2Bzep5IDxbcnCeuOxjzrPF/et3URy9Bv1WTRi" crossorigin="anonymous">
{css}
</head>

<body>
  <div class="container">{content}</div>

  <script src="https://code.jquery.com/jquery-3.6.1.min.js"
    integrity="sha256-o88AwQnZB+VDvE9tvIXrMQaPlFFSUTR+nldQm1LuPXQ=" crossorigin="anonymous"></script>
  <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.2.2/dist/js/bootstrap.bundle.min.js"
    integrity="sha384-OERcA2EqjJCMA+/3y+gxIOqMEjwtxJY7qPCqsdltbNJuaOe923+mo//f6V8Qbsw3"
    crossorigin="anonymous"></script>
{js}
</body>
</html>
    """.format(
        content=content(),
        css=stylesheet(),
        js=javascript(),
    )
