function test(req){
  source = req.body.get('domain');
  sink(source);
}