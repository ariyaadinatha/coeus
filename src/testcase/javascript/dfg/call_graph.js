function test(req){
  const {
    source
  } = req.params;
  
  sink(source);
}

function sink(command){
  eval(command);
}