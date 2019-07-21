const express = require('express');
const path = require('path');
const fs = require('fs');
const app = express();
const uploadModule = require('./uploader');
const multer = require('multer')({ limits: { fieldSize: 20000000} });
const MongoClient = require('mongodb').MongoClient;
const Queue = require('./queue');


const url = 'mongodb://localhost/server';

const callbacks = new Queue();
const cmdQueue = new Queue();
let _db = null;

MongoClient.connect(url, { poolSize: 10, connectTimeoutMS: 0, socketTimeoutMS: 0 }, (err, db) => {
	if(err)
	{
		console.log(err);
		process.exit(-1);
	}

	// callbacks.forEach(fn => fn(db));
	_db = db;

	dequeueEvent();
});

function addToQueue(fn, callback = ()=>{}, errCb = ()=>{}) {

    return;
	if(!_db)
		cmdQueue.enqueue([fn, callback, errCb]);
	else {
		if(cmdQueue.size === 0) {
			processItem([fn, callback, errCb]);
		} else {
			cmdQueue.enqueue([fn, callback, errCb])
		}
	}

}

function dequeueEvent() {
	if(cmdQueue.size === 0)
		return;

	const val = cmdQueue.dequeue();
    processItem(val);
}

function processItem([fn, callback, errCb]) {
   fn(_db).then((r) => {
        callback(r);
        console.log('done', cmdQueue.size);
		dequeueEvent();
	},
    (e) => {
		console.log("OMG");
		errCb(e);
        dequeueEvent();
	});
}

function dbCall(fn) {
	if(_db)
		fn(_db);
	else
		callbacks.enqueue(fn);
}

function dbClose() {
	dbCall((db) => db.close());
}


const style = `
<style>
.imgsqr{
width: 256px;
height: 256px;
display: inline-block;
}
.txt{
display: block;
position: absolute;
width: 236px;
padding: 10px;
background-color: rgba(0,0,0,0.2);
font-family: sans-serif;
color: white;
}
.lnk {
color: white;
}
.detail-img{
width: 256px;
height: 256px;
display: inline-block;
}
.floating {
margin-top: 100px;
margin-left: 10px;
/* height: 200px; */
position: absolute;
background-color: rgba(255, 255, 255, 0.5);
font-family: sans-serif;
}
.levelindicator.correct {
    background-color: green;
}
.levelindicator {
position: absolute;
background-color: yellow;
height: 5px;
}
.invisible {
opacity: 0;
}
.incorrect {
	background-color: rgba(255, 0, 0, 0.5) !important;
}
</style>
<script>
function mover(e) {
	$(e).removeClass('invisible');
}
function mout(e) {
	$(e).addClass('invisible');
}
</script>
<script src='https://code.jquery.com/jquery-3.1.1.min.js' integrity="sha256-hVVnYaiADRTO2PzUGmuLJr8BLUSjGIZsDYGmIJLv2b8=" crossorigin="anonymous"></script>
`



const nameToImagesMap = {};
const imageToHtmlMap = {};
const imageToDetailNameMap = {};

const lvlMap = ['Kingdom', 'Phylum', 'Class', 'Order', 'Family', 'Genus', 'Species'];

const readline = require('readline');



dbCall(db => console.log('db connected'));
dbCall(db => {
	db.collection('test').insertOne({a: 1}, (e, r) => {
		console.log('inserted');
	})
})

if(process.argv.indexOf('redodb') >= 0)
	redoDB();

function redoDB() {

	console.log('redoing database!');

	const rl = readline.createInterface({
	  input: fs.createReadStream('/home/jeff/Workspace/MultiLevelSoftmax/output.csv')
	});

	addToQueue(db => db.collection('nameToImages').remove({}));
    addToQueue(db => db.collection('imageToDetailName').remove({}));

	rl.on('line', (v) => {

	  	if(!v.trim())
			return;

		const firstSplit = v.split('|_|');

		const desc = firstSplit[0];
		const fileInfo = firstSplit[1];


		const secondSplit = desc.split('_._');
		if(secondSplit.length <= 34)
			return;
		const name = secondSplit[26].split(' ').map(v => v.toLowerCase()).join('.');
	    

		const fileSplit = fileInfo.split('_._');
		if(fileSplit.length <=  2)
			return;;
		const link = fileSplit[2];

	    const sliced = secondSplit.slice(28, 34);
	    let initial = 'init'; // eukaryota

	    sliced.map((v) => v.toLowerCase()).forEach((v) => {
			const tname = initial + '.' + v;
			// if(!nameToImagesMap[tname])
			// 	nameToImagesMap[tname] = [];

			// nameToImagesMap[tname].push(link);

			// assumption - mongodb operates queries on a FIFO basis.
			addToQueue(db => {
		  		const col = db.collection('nameToImages');
		  		return col.findOne({"name": name}, {});
            },
                (r) => {
		  			if(!r) {
		  				addToQueue(db => db.collection('nameToImages').insertOne({"name": tname, "images": [link]}));
		  			} else {
		  				addToQueue(db => db.collection('nameToImages').updateOne({"name": tname}, {$push: {"images": link}}));
		  			}
		  		});

			initial = v;        
	    });

	  	addToQueue(db => {
	  		const col = db.collection('nameToImages');
	  		return col.findOne({"name": name}, {});
        }, (r) => {
	  			if(!r) {
	  				addToQueue(db => db.collection('nameToImages').insertOne({"name": name, "images": [link]}))
	  			} else {
	  				addToQueue(db => db.collection('nameToImages').updateOne({"name": name}, {$push: {"images": link}}));
	  			}
        });

        addToQueue(db => db.collection('imageToDetailName').insertOne({"link": link, "details": secondSplit, "name": name}));
	  	

	});
}




function make_link(name) {
	return "<a class='lnk' href='/details/by-name/" + name + "'> " + name + "</a>"
}

function make_search_link(name) {
	return "<a class='lnk' href='http://google.com/search?q=" + name + "'> " + "(search)" + "</a>"
}

function addHtmlEntry(name, classified_label, true_label, hierarchy, probability, isCorrect, level) {
	const out = '<div class="imgsqr">\n' + 
	'<span class="txt' + (isCorrect ? '' : ' incorrect') + '">' + 'expected: ' + make_link(true_label) + make_search_link(true_label) + ', classified: ' + make_link(classified_label) + make_search_link(classified_label) + '(' + probability.toPrecision(3) + ') ' + lvlMap[level] + '</span>\n' + '<span class="levelindicator' + (level == 6 ? ' correct' : '') + '" style="width: ' + Math.floor(256 * ((level + 1.0) / 7.0)) + 'px"></span>' +
  processHierarchy(hierarchy) +

  "<a href='/details/" + name + "'> <img src='/" + name + "' title='" + 'expected: ' + true_label + ', classified: ' + classified_label + "'> </img></a>\n" +
	'</div>\n'

    imageToHtmlMap[name] = out;
	return out;
}

function processHierarchy(info) {
	let layers = info.split('#');

	layers = layers.reverse().map((v) => {
		const items = v.split(',');
		let thisItem = '';
		let matching = false;
		if(items.length > 1 && items[0] == items[1]) {
			matching = true;
			thisItem = items[0];
		} else {
			thisItem = items.join(' vs. ');
		}
		let output;
		if(matching) {
			output = "<span style='color: green'>" + thisItem + "</span>";
		} else {
			output = "<span style='color: red'>" + thisItem + "</span>";
		}

    return output;
	});

	return `<div class='floating invisible' onmouseover="mover(this)" onmouseout = "mout(this)">` + layers.join("<br/>") + "</div>";
}
function sendPage(req, res) {

	fs.readFile('./html.html', {encoding: 'utf-8'}, (err, contents) => {

		const body = contents.split('\n').slice(0, -1).map((val) => {
			const splitted = val.split('|');
			link = splitted[0];
			classified = splitted[1];
			trueLabel = splitted[2];
      		hierarchy = splitted[3];

			probability = parseFloat(splitted[4]);
			isCorrect = splitted[5] == 'True';
			level = parseInt(splitted[6]);
			return addHtmlEntry(link, classified, trueLabel, hierarchy, probability, isCorrect, level);
		});
       
        let filtered = body; 
        if(req.params.filter)
		    filtered = filtered.filter((v) => v.indexOf(req.params.filter) >= 0);
        if(req.params.correctness)
            filtered = filtered.filter((v) => req.params.correctness == 'correct' ? (v.indexOf('incorrect') == -1) : (v.indexOf('incorrect') >= 0));
        
        res.send(style + filtered.join('\n'));
	});
}

function sendHistogram(req, res) {

	fs.readFile('./histogram.dat', {encoding: 'utf-8'}, (err, contents) => {

		const body = contents.split('\n').slice(0, -1);

		res.send(style + body.join('<br/>\n'));
	});
}

app.use((req, res, next) => {
	if(fs.existsSync(__dirname + '/down')) {
		res.sendFile(__dirname + '/down_view.html');
	} else {
		next();
	}
})

app.get("/histogram", sendHistogram);

app.get("/details/:name", (req, res) => {

    const name = req.params.name;
	const details = imageToHtmlMap[name];

	if(!name || !details) {
		return res.sendStatus(404);
	}
	res.send(style + details);//details.replace("a href='", "a href='/").replace("img src='", "img src='/"));
})

app.get("/details/by-name/:name", (req, res) => {

	const name = req.params.name;

	if(!name) {
		return res.sendStatus(404);
	}

	dbCall(db => {

		let done = 0;
		const incr = () => {done += 1};
		const decr = (fn) => {done -= 1; if(done == 0) fn()};

		db.collection('nameToImages').findOne({'name': name}, {}, (e, r) => {
			if(!r)
				return res.sendStatus(404);

			res.write(style + "\n");
			r.images.forEach((v) => {
				incr();
				db.collection('imageToDetailName').findOne({'link': v}, {}, (de, dr) => {
					const details = dr ? dr.details : []; //imageToDetailNameMap[v][0] || [];
			        res.write("<div class='detail-img'><img src='/" + v + ".jpeg' title='" + details.join(', ') + "'></div>\n");
					decr(() => res.end());
				});
			});			
		})
	})
});

app.get("/contains", (req, res) => {
	res.sendFile(__dirname + '/contains_view.html');
})

app.get("/all-species", (req, res) => {
    res.send(Object.keys(nameToImagesMap)
            .map(x => [x, nameToImagesMap[x].length])
            .filter(([k, count]) => count >= 100)
            .map(([k, c]) => k.split('.').join(' ') + ', instances: ' + c)
            .sort()
            .join(" <br/> \n"));
});

app.get("/contains/:name", (req, res) => {

	const name = req.params.name
	.replace(/\./g, ' ')
	.split(' ')
	.map(x => x.toLowerCase())
	.join('.');

	if(!name || !nameToImagesMap[name]) {
		return res.send(0 + '');
	}

	res.send(nameToImagesMap[name].length + '');
});





app.get("/html.html", sendPage);
app.get("/", sendPage);
app.get("/filter/:filter", sendPage);
app.get("/filter/:filter/:correctness", sendPage);

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


app.use(
    "/", //the URL throught which you want to access to you static content
    express.static(__dirname) //where your static content is located in your filesystem
);
app.get("/:fname", (req, res) => {
	res.sendFile("/home/jeff/images/" + req.params.fname)
});


uploadModule.readPipe();


app.listen(80); //the port you want to use
