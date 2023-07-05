const test = (req) => {
  source = req.body.get('domain');
  sink(source);
}

const sink = (command) => {
  eval(command);
}