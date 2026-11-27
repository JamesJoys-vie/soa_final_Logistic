import { totalBoxes } from '../utils/format';

export default function AssignmentSummary({ assignment }) {
  return (
    <span>
      Xe <b>{assignment.plate}</b>, đến <b>{assignment.destination}</b>, tổng <b>{totalBoxes(assignment.lines)}</b> thùng
    </span>
  );
}
