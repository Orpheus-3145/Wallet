CREATE PROCEDURE REFRESH_WORK_COSTS
AS

DECLARE 
@TOTAL_MONTH_COST AS INT,
@TOTAL_MONTH_REFUND AS INT

SET @TOTAL_MONTH_COST = (SELECT SUM(IMPORTO) AS TOTAL FROM MOVIMENTI MV INNER JOIN SPESE_LAVORO SF ON SF.ID_MOV = MV.ID WHERE MESE = MONTH(GETDATE()) GROUP BY IMPORTO)
SET @TOTAL_MONTH_REFUND = (SELECT RIMBORSO_SPESE FROM STIPENDI WHERE MESE = MONTH(GETDATE()))

IF @TOTAL_MONTH_COST = @TOTAL_MONTH_REFUND 
	BEGIN

	DECLARE @ID_STP AS NVARCHAR
	SET @ID_STP = (SELECT ID FROM STIPENDI WHERE MESE = MONTH(GETDATE()))
	UPDATE SPESE_LAVORO SET RIMBORSATO = 1, ID_STIPENDIO = @ID_STP WHERE MESE = MONTH(GETDATE())

	END
ELSE
	PRINT 'ERRORE NEL RIMBORSO SPESE!!'
