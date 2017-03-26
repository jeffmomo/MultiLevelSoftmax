const fs = require('fs');

let imgIndex = 0;

// maps from index to number array
const classified = {};
const awaitings = {};

let numEnqueued = 0;
let numDequeued = 0;
let lastDequeue = 0;

function readPipe() {
	fs.open('/home/jeff/Workspace/MultiLevelSoftmax/outpipe', 'r', (err, file) => {
		if(err) {
			console.log(err);

			return fs.close(file, (err, done) => 
			{
				readPipe();
			});
		}

		fs.readFile(file, (err, content) => {
			// TODO: It is possible that given tiny images the pipe may contain multiple classifications. Deal with this later
			if(err)
				console.log(err)

			const contentString = content.toString('utf-8');
			const splitted = contentString.split(",");
			// (leaf_prob, leaf, dijkstra_prob, dijkstra_node, dijkstra_lvl, index, img_data, _, name, prob, name, prob, name, prob, name, prob, name, prob)
            
            const index = splitted[5];
            splitted[splitted.length - 1] = splitted[splitted.length - 1].replace('>>>EOF<<<', '');
            
            if(awaitings[index]) {
                awaitings[index](splitted);
                delete awaitings[index];
            } else {
			    classified[index] = splitted;
            }

            numDequeued += 1;

            readPipe();
		})
	});
}



function writePipe(imgIndex, content, priors = '') {
	const file = fs.openSync('/home/jeff/Workspace/MultiLevelSoftmax/pipe', 'w');
    fs.writeSync(file, content + '>>>INDEX<<<' + imgIndex + '|' + priors + '>>>EOF<<<');
    fs.closeSync(file);
}

function fill(template, fillers) {
	return Object.keys(fillers).reduce((accum, a) => {
		return accum.split('{{' + a + '}}').join(fillers[a]);
	}, template)
}


function upload(req, res) {
	// console.log(req.file.buffer.toString('base64'));

	// console.log(req.body);

    // handle cases where no image provided.. 
    const base64Img = req.file ? req.file.buffer.toString('base64') : req.body.image_base64.split(',')[1];

    // console.log(base64Img === req.file.buffer.toString('base64'));


	writePipe(imgIndex, base64Img, req.body.priors ? req.body.priors : '');
	console.log(req.body.priors);

	const savedImgIndex = imgIndex;
	imgIndex += 1;

	console.log(imgIndex);

	numEnqueued += 1;

	fs.readFile('./classified_view.html', {encoding: 'utf-8'}, (err, contents) => {
		const queued = numEnqueued - lastDequeue - 1;
		const timeRemaining = queued * 0.5;

		const body = fill(contents, {queued, timeRemaining, imgIndex: savedImgIndex});
		

		res.send(body);
	});
}

function waitOnClassification(req, res) {

    const waitingOnLabel = req.params.label;
    
    
    const onAvailableFn = (result) => {
        lastDequeue = parseInt(result[5]);
        console.log('available');
        res.json(result);
    };

    if(classified[waitingOnLabel]) {
        console.log('classification already available'); 
        
        onAvailableFn(classified[waitingOnLabel]);
        delete classified[waitingOnLabel];

    } else {

        awaitings[waitingOnLabel] = onAvailableFn;

    }

}


module.exports = {
	upload: upload,
	readPipe: readPipe,
    waitingOnClassification: waitOnClassification,
}
