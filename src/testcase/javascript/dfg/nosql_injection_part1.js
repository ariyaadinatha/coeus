const AllocationsDAO = function(db){
    const allocationsCol = db.collection("allocations");

    this.getByUserIdAndThreshold = (userId, threshold, callback) => {
        const parsedUserId = parseInt(userId);

        const searchCriteria = () => {
            return {
                $where: `this.userId == ${parsedUserId} && this.stocks > '${threshold}'`
            };
        };

        allocationsCol.find(searchCriteria())
    };
};

module.exports.AllocationsDAO = AllocationsDAO;