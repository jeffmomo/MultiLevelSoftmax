const fs = require('fs');
const Adapter = require('./adapter');

let imgIndex = 0;

// maps from index to number array
const classified = {};
const awaitings = {};

let numEnqueued = 0;
let numDequeued = 0;
let lastDequeue = 0;


const adapter = new Adapter('/home/jeff/Workspace/models/slim/done_pipe.fifopipe', '/home/jeff/Workspace/models/slim/classify_pipe.fifopipe');

function pollCallback(content) {
    const contentString = content.toString('utf-8');
    const splitted = contentString.split(",");
    // (leaf_prob, leaf, dijkstra_prob, dijkstra_node, dijkstra_lvl, index, img_data, _, name, prob, name, prob, name, prob, name, prob, name, prob)

    const index = splitted[5];
    splitted[splitted.length - 1] = splitted[splitted.length - 1].replace('>>>EOF<<<', '');

    if (awaitings[index]) {
        awaitings[index](splitted);
        delete awaitings[index];
    } else {
        classified[index] = splitted;
    }

    numDequeued += 1;
}

function doPoll() {
    adapter.poll(pollCallback());
}


function writePipe(imgIndex, content, priors = '') {
    adapter.write(content + adapter.INDEX_SEPARATOR + imgIndex + '|' + priors + adapter.EOF_SEPARATOR);
}

function fill(template, fillers) {
    return Object.keys(fillers).reduce((accum, a) => {
        return accum.split('{{' + a + '}}').join(fillers[a]);
    }, template)
}


function upload(req, res) {
    // handle cases where no image provided.. 
    const base64Img = req.file ? req.file.buffer.toString('base64') : req.body.image_base64.split(',')[1];

    writePipe(imgIndex, base64Img, req.body.priors ? req.body.priors : '');

    const savedImgIndex = imgIndex;
    imgIndex += 1;
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

    if (classified[waitingOnLabel]) {
        onAvailableFn(classified[waitingOnLabel]);
        delete classified[waitingOnLabel];
    } else {
        awaitings[waitingOnLabel] = onAvailableFn;

    }

}

module.exports = {
    upload: upload,
    poll: doPoll,
    waitingOnClassification: waitOnClassification,
};
