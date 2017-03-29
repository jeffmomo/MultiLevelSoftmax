const express = require('express');
const path = require('path');
const fs = require('fs');
const app = express();
const uploadModule = require('./uploader_new');
const multer = require('multer')({ limits: { fieldSize: 20000000} });

// const style = `
// <style>
// .imgsqr{
// width: 256px;
// height: 256px;
// display: inline-block;
// }
// .txt{
// display: block;
// position: absolute;
// width: 236px;
// padding: 10px;
// background-color: rgba(0,0,0,0.2);
// font-family: sans-serif;
// color: white;
// }
// .lnk {
// color: white;
// }
// .detail-img{
// width: 256px;
// height: 256px;
// display: inline-block;
// }
// .floating {
// margin-top: 100px;
// margin-left: 10px;
// /* height: 200px; */
// position: absolute;
// background-color: rgba(255, 255, 255, 0.5);
// font-family: sans-serif;
// }
// </style>
// <script src='https://code.jquery.com/jquery-3.1.1.min.js' integrity="sha256-hVVnYaiADRTO2PzUGmuLJr8BLUSjGIZsDYGmIJLv2b8=" crossorigin="anonymous"></script>
// `
//

app.use((req, res, next) => {
	if(fs.existsSync(__dirname + '/down')) {
		res.sendFile(__dirname + '/down_view.html');
	} else {
		next();
	}
})


app.get("/classify", (req, res) => {
	res.sendFile(__dirname + "/upload_advanced_view.html");
});
app.get('/classify-mobile', (req, res) => {
    res.sendFile(__dirname + '/upload_view.html');
});
app.get("/classify-advanced", (req, res) => {
	res.sendFile(__dirname + "/upload_advanced_view.html");
});
app.post("/classify-upload", multer.single('example'), uploadModule.upload);
app.get("/waiting/:label", uploadModule.waitingOnClassification);


// app.use(
//     "/", //the URL throught which you want to access to you static content
//     express.static(__dirname) //where your static content is located in your filesystem
// );
// app.get("/:fname", (req, res) => {
// 	res.sendFile("/home/jeff/images/" + req.params.fname)
// });

uploadModule.poll();


app.listen(80); //the port you want to use
