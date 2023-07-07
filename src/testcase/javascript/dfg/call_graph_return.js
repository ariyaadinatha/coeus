function pass(req) {
  const {
    source
  } = req.params;

  return source;
}

function test(req){
  source = pass(req);
  sink(source);
}

function sink(command){
  eval(command);
}