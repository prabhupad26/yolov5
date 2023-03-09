const content = document.getElementById('content');
const loadingOverlay = document.getElementById('loading-overlay');
const imageRadio = document.querySelector('input[value="image_mode"]');
const videoRadio = document.querySelector('input[value="video_mode"]');
const video = document.getElementById("video_main");
const img = document.getElementById("img_main");
const mediaContainer = document.getElementById('media-container');

const play_btn = document.getElementById('play_btn');
const stlIds = ['stl_1', 'stl_2'];
stlIds.forEach(stlId => {
  const video = videojs(`video_${stlId}`);
  video.currentTime(0);
});
play_btn.addEventListener('click', () => {
    // Send a GET request to the Flask server and read the response
  showLoadingOverlay();
  const selectedOption = document.getElementById("capability_option").value;
  const model_type = document.getElementById("model_type").value;
  const selected_mode = document.querySelector('input[name="radio_btn"]:checked').value;
  const url = `http://127.0.0.1:5000/get_simulation_results?option=${selectedOption}&model_type=${model_type}&exec_mode=${selected_mode}`;
  fetch(url)
    .then(response => response.json())
    .then(data => {
      hideLoadingOverlay();
      if (selected_mode === 'video_mode'){
        // Process the data object
        const status = data[0]['stl_1']['status'];
        const timeRemaining = data[0]['stl_1']['time_remaining'];
        console.log(`Status: ${status}, Time remaining: ${timeRemaining}`);
        processData(data);
      }
      else {
        const img_lane1 = document.getElementById('img_lane1');
        const img_lane2 = document.getElementById('img_lane2');
        img_lane1.src = `static/videos/scenario_1_image_mode/output/${data.lane1.img_name}`;
        img_lane2.src = `static/videos/scenario_1_image_mode/output/${data.lane2.img_name}`;
        document.getElementById(`${stlIds[0]}`).src = `static/images/trafficLight_${data.lane1.tl_status}.png`;
        document.getElementById(`${stlIds[1]}`).src = `static/images/trafficLight_${data.lane2.tl_status}.png`;
      }
    })
    .catch(error => console.error(error));
});


function processData(data) {

  // Loop through each element in the data object
  Object.keys(data).forEach(key => {
    // Wait for 1 second
    setTimeout(() => {
      // Loop through each STL ID
      const times = [];
      const element_ids = [];

      stlIds.forEach(stlId => {
        // Get the status for the current STL
        const status = data[key][stlId]['status'];

        // Replace the image based on the status for the current STL
        const img = document.getElementById(`${stlId}`);
        const video = videojs(`video_${stlId}`);
        times.push(data[key][`${stlId}`]['time_remaining']);
        element_ids.push(`timer_${stlId}`);
        // simulation for adding new vehicles
        if (parseInt(data[key][stlId]['skip_scene']) > 0){
          video.currentTime(parseInt(data[key][stlId]['skip_scene']));
        }
        if (status === 'green' & data[key][`${stlId}`]['time_remaining'] >= 5) {
          img.src = 'static/images/trafficLight_green.png';
          if (video.paused){
            video.play();
          }
        } else if (status === 'red' & data[key][`${stlId}`]['time_remaining'] >= 5) {
          img.src = 'static/images/trafficLight_red.png';
          video.pause();
        }
        else{
          img.src = 'static/images/trafficLight_yellow.png';
          video.playbackRate(0.5);
        }
      });
      startTimers(times[0], times[1], element_ids[0], element_ids[1]);
    }, 1000 * key);
  });
};

function startTimers(time1, time2, elementId1, elementId2) {
  const element1 = document.getElementById(elementId1);
  const element2 = document.getElementById(elementId2);

  element1.innerHTML = `00:${time1}`;
  element2.innerHTML = `00:${time2}`;

}

// Show the loading overlay
function showLoadingOverlay() {
  loadingOverlay.style.display = 'flex';
}

// Hide the loading overlay
function hideLoadingOverlay() {
  loadingOverlay.style.display = 'none';
}

imageRadio.addEventListener('click', () => {
  mediaContainer.style.display = 'block';
  img.style.display = 'block';
  video.style.display = 'none';
});

videoRadio.addEventListener('click', () => {
  mediaContainer.style.display = 'block';
  img.style.display = 'none';
  video.style.display = 'block';
});


// code for uploading the video file
// var upload_lane_1 = document.getElementById('lane1_feed');
// var upload_lane_2 = document.getElementById('lane2_feed');
// var video_player_1 = videojs('video_stl_1');
// var video_player_2 = videojs('video_stl_2');

// upload_lane_1.addEventListener('submit', function(event) {
//     event.preventDefault();
//     var file = document.getElementById('input_lane1_feed').files[0];
//     var formData = new FormData();
//     formData.append('file', file);

//     var xhr = new XMLHttpRequest();
//     xhr.open('POST', '/upload', true);
//     xhr.onload = function() {
//         if (xhr.status === 200) {
//             var response = JSON.parse(xhr.responseText);
//             video_player_1.src(response.fileUrl);
//             video_player_1.load();
//         }
//     };
//     xhr.send(formData);
// });

// upload_lane_2.addEventListener('submit', function(event) {
//   event.preventDefault();
//   var file = document.getElementById('input_lane2_feed').files[0];
//   var formData = new FormData();
//   formData.append('file', file);

//   var xhr = new XMLHttpRequest();
//   xhr.open('POST', '/upload', true);
//   xhr.onload = function() {
//       if (xhr.status === 200) {
//           var response = JSON.parse(xhr.responseText);
//           video_player_2.src(response.fileUrl);
//           video_player_2.load();
//       }
//   };
//   xhr.send(formData);
// });