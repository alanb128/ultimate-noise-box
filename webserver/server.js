const express = require('express');
const app = express();
const {env} = require('process');
const fs = require('fs');

const http = require('http');
const path = require('path');
const url = require('url');

app.set("view engine", "ejs");
app.set("views", __dirname + "/views");

const redis = require('redis');
const { promisify } = require('util');
const client = redis.createClient({
    host: 'redis',
    port: 6379
});

client.on('error', err => {
  console.log('Error ' + err);
});


let media_path = env.MEDIA_PATH || "/data/my_data/noise/";

// Enable HTML template middleware
app.engine('html', require('ejs').renderFile);

// Enable static CSS styles
app.use(express.static('styles'));

// Enable access to wav files
app.use("/public", express.static(media_path));

// For processing forms
app.use(express.urlencoded({ extended: true}))


// reply to home page request
app.get('/', function (req, res) {
  //res.render('index');
  client.mget(['p1', 'p2', 'p3', 'p4'], (err, reply) => {
  getImages(media_path, function (err, files, hasimage) {
    var imageLists = '<table class="w3-table w3-striped w3-bordered" id="tblMain">';
    for (var i=0; i<files.length; i++) {
        imageLists += '<tr class="w3-theme"><td width="10%"><img src="/public/' + hasimage[i] + '"';
        //if (hasimage[i] == 0) {
        //  imageLists += 'default.jpg';
        //} else {
        //  imageLists += files[i] + '.jpg">';
        //}
        imageLists += '</td><td style="text-align: left;"><h2>  ' + files[i].replace('_', ' ') +  ' </h2><br />';
        imageLists += '<a class="w3-button w3-circle w3-small w3-blue" onclick="playsound(\'' + files[i] + '\')"><i class="fas fa-play"></i></a>&nbsp;&nbsp;&nbsp;';
        imageLists += '<a class="w3-button w3-circle w3-small w3-blue" onclick="preset(\'' + files[i] + '\', 1)">1</a>&nbsp;&nbsp;&nbsp;';
        imageLists += '<a class="w3-button w3-circle w3-small w3-blue" onclick="preset(\'' + files[i] + '\', 2)">2</a>&nbsp;&nbsp;&nbsp;';
        imageLists += '<a class="w3-button w3-circle w3-small w3-blue" onclick="preset(\'' + files[i] + '\', 3)">3</a>&nbsp;&nbsp;&nbsp;';
        imageLists += '<a class="w3-button w3-circle w3-small w3-blue" onclick="preset(\'' + files[i] + '\', 4)">4</a> ';
        imageLists += '</td></tr>';
      }
      imageLists += '</table>';
      //res.writeHead(200, {'Content-type':'text/html'});
      //res.end(imageLists);
      console.log("rendering")
      var presets = []
      // TODO: handle null reply below...
      presets = reply
      console.log(presets)
      res.render('index', { assets: imageLists, prlist: presets });
    });
    }); // client.get
});

app.post('/play', function (req, res) {
  console.log('POST')
  console.dir(req.body)
  PostCode('/play/' + req.body.filename + '/');
  res.redirect('back');
});

app.post('/stop', function (req, res) {
  console.log('POST')
  //console.dir(req.body)
  PostCode('/stop/');
  res.redirect('back');
});

app.post('/preset', function (req, res) {
  console.log('POST')
  //console.dir(req.body)
  
  client.set('p' + req.body.preset, req.body.filename, (err, reply) => {
    if (err) throw err;
    console.log(reply);
  });

  res.redirect('back');
});

//start a server on port 80 and log its start to our console
var server = app.listen(80, function () {

  var port = server.address().port;
  console.log('Express server listening on port ', port);

});

//get the list of wav files in the image dir
function getImages(imageDir, callback) {
  var fileType = '.wav', imageType = '.jpg',
    files = [], hasimage = [], i;
  fs.readdir(imageDir, function (err, list) {
    for(i=0; i<list.length; i++) {
      if(path.extname(list[i]) === fileType) {
        img_name = path.basename(list[i], fileType)  // just the name, no extension
        files.push(img_name); //store the name into the array files
        img_path = imageDir + img_name + imageType;  // path + name + img ext
        //console.log(img_path);
        //fs.access(img_path, function (err) {
        //  if (err) {
        //    hasimage.push('default.' + imageType)
        //    console.log("The file does not exist.");
        //  } else {
        //    hasimage.push(img_name + imageType);
        //    console.log("The file exists.");
        //  }
        //});
        if(fs.existsSync(img_path)) {
          hasimage.push(img_name + imageType);
          //console.log("The file exists.");
        } else {
          hasimage.push('default' + imageType)
          //console.log('The file does not exist.');
        }
      }
    }
    //console.log(files, hasimage);
    callback(err, files, hasimage);
  });
}

function PostCode(filename) {
  // Build the post string from an object
  var post_data = 'mydata';

  // An object of options to indicate where to post to
  var post_options = {
      host: 'noise',
      port: '5000',
      path: filename,
      method: 'POST',
      headers: {
          'Content-Type': 'application/x-www-form-urlencoded',
          'Content-Length': Buffer.byteLength(post_data)
      }
  };

  // Set up the request
  var post_req = http.request(post_options, function(res) {
      res.setEncoding('utf8');
      res.on('data', function (chunk) {
          console.log('Response: ' + chunk);
      });
  });

  post_req.on('error', error => {
  console.error(error)
  })

  // post the data
  post_req.write(post_data);
  post_req.end();

}

