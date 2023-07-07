function AllocationsHandler(db) {
    const allocationsDAO = new AllocationsDAO(db);

    this.displayAllocations = (req, res, next) => {
        const {
            userId
        } = req.params;
        const {
            threshold
        } = req.query;

        allocationsDAO.getByUserIdAndThreshold(userId, threshold, () => {
            console.log('test');
        });
    };
}

module.exports = AllocationsHandler;
