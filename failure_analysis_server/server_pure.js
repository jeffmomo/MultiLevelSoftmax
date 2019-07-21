const express = require('express');
const path = require('path');
const fs = require('fs');
const app = express();
const uploadModule = require('./uploader_new');
const multer = require('multer')({ limits: { fieldSize: 20000000} });

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


app.listen(8000); //the port you want to use
