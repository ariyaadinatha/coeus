const loggedInUser = req.cookies.token

models.User.findByPk(loggedInUser).then(user => {
    const code = user
    username = eval(code)
  })