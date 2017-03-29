const fs = require('fs');
const Adapter = require('./Adapter');

class FIFOAdapter extends Adapter {



    constructor(towards_webserver_resource, towards_classifier_resource) {
        this.INDEX_SEPARATOR = '>>>INDEX<<<';
        this.EOF_SEPARATOR = '>>>EOF<<<';

        this.towards_webserver_resource = towards_webserver_resource;
        this.towards_classifier_resource = towards_classifier_resource;
    }

    poll(callback) {

        fs.open(this.towards_webserver_resource, 'r', (err, file) => {

            if (err) {
                console.error(err);

                return fs.close(file, (err, done) => {
                    this.poll(callback);
                });
            }

            fs.readFile(file, (err, content) => {
                // TODO: It is possible that given tiny images the pipe may contain multiple classifications. Deal with this later
                if (err)
                    console.error(err);

                callback(content);
                this.poll(callback);
            })
        });
    }

    write(content, callback) {
        fs.open(this.towards_classifier_resource, 'w', (err, file) => {

            if (err) {
                return callback(err, null);
            }

            fs.write(file, content, (err, done) => {
                callback(err, done);
                fs.close(file);
            });
        });
    }

}

module.exports = FIFOAdapter;