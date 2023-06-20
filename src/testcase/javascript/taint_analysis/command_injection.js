app.get('/', (req, res) => {
  const folder = req.query.folder;
  if (folder) {
    // Run the command with the parameter the user gives us
    exec(`ls -l ${folder}`, (error, stdout, stderr) => {
      let output = stdout;
      if (error) {
        // If there are any errors, show that
        output = error; 
      }
      res.send(
        pug.renderFile('./pages/index.pug', {output: output, folder: folder})
      );
    });
  } else {
    res.send(pug.renderFile('./pages/index.pug', {}));
  }
});