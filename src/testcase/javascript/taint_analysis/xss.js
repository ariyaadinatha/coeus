doc.website = ESAPI.encoder().encodeForHTML(doc.website);
// fix it by replacing the above with another template variable that is used for 
// the context of a URL in a link header
// doc.website = ESAPI.encoder().encodeForURL(doc.website)

return res.render("profile", {
    ...doc,
    environmentalScripts
});