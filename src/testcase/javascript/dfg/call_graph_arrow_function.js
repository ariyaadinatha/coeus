const test = (req) => {
  const {
    source
  } = req.params;
  
  sink(source);
}

const sink = (command) => {
  eval(command);
}