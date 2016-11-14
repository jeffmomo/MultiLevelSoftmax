const fs = require('fs');

while(true) {
    const file = fs.openSync('./pipe', 'w');
    fs.writeSync(file, ((Math.random() * 100)|0) + '>>>EOF<<<');
    fs.closeSync(file);
}